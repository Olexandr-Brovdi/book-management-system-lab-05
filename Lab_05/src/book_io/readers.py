"""Streaming CSV / JSON Lines adapters behind one structural interface."""

import csv
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Protocol

from book_io.exceptions import DataImportError
from book_io.models import SourceRow
from book_io.validators import FIELDS


class Importer(Protocol):
    def read(self, path: Path) -> Iterator[SourceRow]: ...


class CsvImporter:
    def read(self, path: Path) -> Iterator[SourceRow]:
        try:
            with path.open(encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle, strict=True)
                if reader.fieldnames is None or tuple(reader.fieldnames) != FIELDS:
                    raise DataImportError(
                        "CSV header must be isbn,title,author,year,pages"
                    )
                for row in reader:
                    yield SourceRow(reader.line_num, row)
        except (OSError, UnicodeError, csv.Error) as error:
            raise DataImportError(
                "Cannot read a structurally valid CSV input"
            ) from error


class JsonLinesImporter:
    def read(self, path: Path) -> Iterator[SourceRow]:
        try:
            with path.open(encoding="utf-8-sig") as handle:
                for number, line in enumerate(handle, 1):
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        yield SourceRow(number, None, "Invalid JSON on this line")
                    else:
                        yield SourceRow(number, data)
        except (OSError, UnicodeError) as error:
            raise DataImportError("Cannot read JSON Lines input") from error


def select_importer(format_name: str) -> Importer:
    if format_name == "csv":
        return CsvImporter()
    if format_name == "jsonl":
        return JsonLinesImporter()
    raise DataImportError("Unsupported input format")
