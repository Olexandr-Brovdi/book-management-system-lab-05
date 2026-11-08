"""Reliability requirements, failure paths and streaming semantics."""

import io
import json
import logging
import tempfile
import unittest
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import yaml

from book_io.config import load_config
from book_io.datasets import generate_csv, isbn_for
from book_io.exceptions import (
    ConfigurationError,
    DataExportError,
    DataImportError,
    RecordValidationError,
)
from book_io.exporters import JsonExporter, JsonLinesExporter
from book_io.logging_config import configure_logging
from book_io.models import (
    AppConfig,
    Book,
    ImportStatistics,
    LoggingConfig,
    ProcessingConfig,
    SourceRow,
)
from book_io.readers import CsvImporter, JsonLinesImporter
from book_io.services import import_books, process
from book_io.validators import parse_book, valid_isbn

POLICY = ProcessingConfig(1800, 2026, True)


class ReliabilityTests(unittest.TestCase):
    def setUp(self):
        logging.getLogger("book_io").addHandler(logging.NullHandler())
        logging.getLogger("book_io").propagate = False
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.input = self.root / "books.csv"
        generate_csv(self.input, 3, 2)
        self.config = AppConfig(
            self.input,
            self.root / "out.json",
            "csv",
            "json",
            POLICY,
            LoggingConfig("INFO", self.root / "run.log"),
            self.root / "summary.json",
        )

    def tearDown(self):
        logger = logging.getLogger("book_io")
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
        self.temp.cleanup()

    def test_tolerant_statistics(self):
        stats = process(self.config)
        self.assertEqual(
            (stats.total, stats.valid, stats.invalid, stats.exported), (5, 3, 2, 3)
        )
        self.assertEqual(
            len(json.loads(self.config.output_path.read_text(encoding="utf-8"))), 3
        )

    def test_strict_preserves_old_output(self):
        self.config.output_path.write_text('["old"]', encoding="utf-8")
        before = self.config.output_path.read_bytes()
        stats = ImportStatistics()
        with self.assertRaises(RecordValidationError):
            process(
                replace(self.config, processing=replace(POLICY, skip_invalid=False)),
                stats,
            )
        self.assertEqual(
            (stats.total, stats.valid, stats.invalid, stats.exported), (4, 3, 1, 0)
        )
        self.assertEqual(before, self.config.output_path.read_bytes())
        self.assertEqual(list(self.root.glob("*.tmp")), [])

    def test_isbn_checks(self):
        self.assertTrue(valid_isbn("0306406152"))
        self.assertTrue(valid_isbn("9780306406157"))
        for invalid in ("123", "9780306406158", "abcdefghij"):
            self.assertFalse(valid_isbn(invalid))

    def test_validation_fields_and_cause(self):
        row = {
            "isbn": isbn_for(1),
            "title": " A ",
            "author": " B ",
            "year": "2000",
            "pages": "12",
        }
        self.assertEqual(parse_book(SourceRow(2, row), POLICY).title, "A")
        for field, value in [
            ("isbn", "x"),
            ("title", ""),
            ("author", " "),
            ("year", "1700"),
            ("pages", "0"),
        ]:
            with self.subTest(field=field), self.assertRaises(RecordValidationError):
                parse_book(SourceRow(2, {**row, field: value}), POLICY)
        try:
            parse_book(SourceRow(2, {**row, "pages": "wrong"}), POLICY)
        except RecordValidationError as error:
            self.assertIsInstance(error.__cause__, ValueError)
            self.assertEqual(error.field, "pages")
        else:
            self.fail("Expected chained validation failure")

    def test_reject_numeric_bool_float(self):
        row = {
            "isbn": isbn_for(1),
            "title": "A",
            "author": "B",
            "year": 2000,
            "pages": True,
        }
        with self.assertRaises(RecordValidationError):
            parse_book(SourceRow(1, row), POLICY)
        with self.assertRaises(RecordValidationError):
            parse_book(SourceRow(1, {**row, "pages": 1.5}), POLICY)

    def test_csv_multiline(self):
        text = "isbn,title,author,year,pages\n" + isbn_for(1) + ',"A\n B",C,2000,10\n'
        handle = io.StringIO(text)
        with (
            patch("pathlib.Path.open", return_value=handle),
            closing(
                import_books(Path("x"), CsvImporter(), POLICY, ImportStatistics())
            ) as books,
        ):
            self.assertEqual(next(books).title, "A B")
        self.assertTrue(handle.closed)

    def test_missing_input_chaining(self):
        with self.assertRaises(DataImportError) as context:
            list(CsvImporter().read(self.root / "missing.csv"))
        self.assertIsInstance(context.exception.__cause__, OSError)

    def test_structural_csv_failure(self):
        self.input.write_text(
            'isbn,title,author,year,pages\n1,"unclosed', encoding="utf-8"
        )
        with self.assertRaises(DataImportError):
            list(CsvImporter().read(self.input))

    def test_wrong_header(self):
        self.input.write_text("wrong,header\n", encoding="utf-8")
        with self.assertRaises(DataImportError):
            list(CsvImporter().read(self.input))

    def test_missing_extra_columns_invalid(self):
        self.input.write_text(
            "isbn,title,author,year,pages\n1,A,B,2000\n1,A,B,2000,5,extra\n",
            encoding="utf-8",
        )
        stats = ImportStatistics()
        self.assertEqual(
            list(import_books(self.input, CsvImporter(), POLICY, stats)), []
        )
        self.assertEqual(stats.invalid, 2)

    def test_atomic_injected_failure(self):
        path = self.root / "out.json"
        path.write_text('["previous"]', encoding="utf-8")

        def broken():
            yield Book(isbn_for(1), "A", "B", 2000, 10)
            raise DataExportError("Injected export failure")

        with self.assertRaises(DataExportError):
            JsonExporter().write(broken(), path)
        self.assertEqual(path.read_text(encoding="utf-8"), '["previous"]')
        self.assertEqual(list(self.root.glob("*.tmp")), [])

    def test_atomic_replace_failure(self):
        path = self.root / "out.json"
        path.write_text("old", encoding="utf-8")
        with (
            patch(
                "book_io.resources.os.replace", side_effect=PermissionError("fixture")
            ),
            self.assertRaises(DataExportError) as context,
        ):
            JsonExporter().write([], path)
        self.assertIsInstance(context.exception.__cause__, PermissionError)
        self.assertEqual(path.read_text(encoding="utf-8"), "old")
        self.assertEqual(list(self.root.glob("*.tmp")), [])

    def test_empty_export(self):
        JsonExporter().write([], self.config.output_path)
        self.assertEqual(json.loads(self.config.output_path.read_text()), [])

    def test_jsonl_roundtrip_and_bad_line(self):
        book = Book(isbn_for(1), "A", "B", 2000, 10)
        path = self.root / "books.jsonl"
        JsonLinesExporter().write([book], path)
        with path.open("a", encoding="utf-8") as handle:
            handle.write("wrong json\n")
        stats = ImportStatistics()
        restored = list(import_books(path, JsonLinesImporter(), POLICY, stats))
        self.assertEqual(restored, [book])
        self.assertEqual((stats.valid, stats.invalid), (1, 1))

    def test_lazy_open_and_close(self):
        handle = io.StringIO(
            "isbn,title,author,year,pages\n" + isbn_for(1) + ",A,B,2000,10\n"
        )
        with patch("pathlib.Path.open", return_value=handle) as opened:
            stream = import_books(Path("x"), CsvImporter(), POLICY, ImportStatistics())
            opened.assert_not_called()
            next(stream)
            stream.close()
            self.assertTrue(handle.closed)

    def raw_config(self):
        return {
            "schema_version": 1,
            "input": {"path": "books.csv"},
            "output": {"path": "new/out.json"},
            "processing": {"min_year": 1800, "max_year": 2026, "skip_invalid": True},
            "logging": {"level": "INFO", "path": "log/application.log"},
        }

    def save_config(self, raw):
        path = self.root / "config.yaml"
        path.write_text(yaml.safe_dump(raw), encoding="utf-8")
        return path

    def test_yaml_config_and_auto_format(self):
        config = load_config(self.save_config(self.raw_config()))
        self.assertEqual(config.input_format, "csv")
        self.assertEqual(config.output_format, "json")
        self.assertEqual(config.input_path, self.input)
        self.assertFalse(config.output_path.parent.exists())
        process(config)
        self.assertTrue(config.output_path.exists())

    def test_yaml_string_false_is_rejected(self):
        raw = self.raw_config()
        raw["processing"]["skip_invalid"] = "false"
        with self.assertRaises(ConfigurationError):
            load_config(self.save_config(raw))

    def test_yaml_invalid_range(self):
        raw = self.raw_config()
        raw["processing"]["min_year"] = 2100
        with self.assertRaises(ConfigurationError):
            load_config(self.save_config(raw))

    def test_missing_bad_yaml_and_missing_section(self):
        with self.assertRaises(ConfigurationError):
            load_config(self.root / "missing.yaml")
        bad = self.root / "bad.yaml"
        bad.write_text("input: [", encoding="utf-8")
        with self.assertRaises(ConfigurationError):
            load_config(bad)
        raw = self.raw_config()
        del raw["input"]
        with self.assertRaises(ConfigurationError):
            load_config(self.save_config(raw))

    def test_path_collision_rejected(self):
        raw = self.raw_config()
        raw["output"]["path"] = "books.csv"
        with self.assertRaises(ConfigurationError):
            load_config(self.save_config(raw))

    def test_logging_and_rotation(self):
        config = LoggingConfig("INFO", self.root / "log.txt", 100, 2)
        configure_logging(config)
        logger = logging.getLogger("book_io")
        for handler in logger.handlers[:]:
            if type(handler) is logging.StreamHandler:
                logger.removeHandler(handler)
                handler.close()
        for _ in range(20):
            logging.getLogger("book_io.tests").info("Repeat fixture event")
        self.assertTrue((self.root / "log.txt.1").exists())
