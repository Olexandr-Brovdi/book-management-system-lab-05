"""Five required reliability experiments with real evidence files."""

import csv
import gc
import json
import subprocess
import sys
import tempfile
import traceback
import tracemalloc
from dataclasses import asdict, replace
from pathlib import Path
from time import perf_counter

import yaml

from book_io.datasets import generate_csv, isbn_for
from book_io.exceptions import DataExportError, RecordValidationError
from book_io.exporters import JsonExporter
from book_io.logging_config import configure_logging
from book_io.models import (
    AppConfig,
    Book,
    ImportStatistics,
    LoggingConfig,
    ProcessingConfig,
    SourceRow,
)
from book_io.resources import logged_operation
from book_io.services import process
from book_io.validators import parse_book


def measure_csv(path: Path, eager: bool) -> dict[str, object]:
    gc.collect()
    tracemalloc.start()
    start = perf_counter()
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if eager:
                records = list(reader)
                count = len(records)
            else:
                count = sum(1 for _ in reader)
        elapsed = perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
        return {"count": count, "seconds": elapsed, "peak_bytes": peak}
    finally:
        tracemalloc.stop()


def configuration_cases(root: Path, results: Path) -> list[dict[str, object]]:
    base = yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8"))
    base["input"]["path"] = str(root / "data/books.csv")
    cases = []
    folder = Path(tempfile.mkdtemp(prefix="config_cases_", dir=root / "data/generated"))
    for name in (
        "missing_config",
        "malformed_yaml",
        "missing_input_key",
        "invalid_year_range",
        "missing_input_file",
        "missing_output_directory",
    ):
        raw = json.loads(json.dumps(base))
        raw["output"]["path"] = str(folder / name / "books.json")
        raw["output"]["summary"] = str(folder / name / "summary.json")
        raw["logging"]["path"] = str(folder / name / "run.log")
        config_path = folder / (name + ".yaml")
        if name == "missing_config":
            config_path.unlink(missing_ok=True)
        elif name == "malformed_yaml":
            config_path.write_text("input: [", encoding="utf-8")
        else:
            if name == "missing_input_key":
                del raw["input"]
            elif name == "invalid_year_range":
                raw["processing"]["min_year"] = 2100
            elif name == "missing_input_file":
                raw["input"]["path"] = str(folder / "absent.csv")
            config_path.write_text(yaml.safe_dump(raw), encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, "-m", "book_io", "--config", str(config_path)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=root,
        )
        expected = 0 if name == "missing_output_directory" else 1
        assert completed.returncode == expected, (name, completed.stderr)
        (results / (name + ".txt")).write_text(
            completed.stdout + completed.stderr, encoding="utf-8"
        )
        cases.append(
            {
                "case": name,
                "exit_code": completed.returncode,
                "output_exists": Path(raw["output"]["path"]).exists(),
            }
        )
    return cases


def run_experiments(root: Path) -> None:
    results = root / "docs/results"
    results.mkdir(parents=True, exist_ok=True)
    folder = root / "data/generated"
    mixed = folder / "mixed_1010.csv"
    generate_csv(mixed, 1000, 10)
    log_path = results / "experiments.log"
    configure_logging(LoggingConfig("INFO", log_path))
    base = AppConfig(
        mixed,
        folder / "tolerant.json",
        "csv",
        "json",
        ProcessingConfig(1800, 2026, True),
        LoggingConfig("INFO", log_path),
        folder / "summary.json",
    )
    policies = []
    for strict in (True, False):
        output = folder / ("strict.json" if strict else "tolerant.json")
        output.write_text('["previous valid output"]', encoding="utf-8")
        before = output.read_bytes()
        config = replace(
            base,
            output_path=output,
            processing=replace(base.processing, skip_invalid=not strict),
        )
        stats = ImportStatistics()
        try:
            process(config, stats)
        except RecordValidationError:
            assert strict
            status = "controlled abort"
        else:
            assert not strict
            status = "success"
        policies.append(
            {
                "mode": "strict" if strict else "tolerant",
                **asdict(stats),
                "status": status,
                "previous_preserved": output.read_bytes() == before,
            }
        )
    assert policies[0]["exported"] == 0 and policies[0]["previous_preserved"]
    assert policies[1]["exported"] == 1000 and policies[1]["invalid"] == 10
    row = {
        "isbn": isbn_for(1),
        "title": "A",
        "author": "B",
        "year": "2000",
        "pages": "wrong",
    }
    try:
        parse_book(SourceRow(2, row), base.processing)
    except RecordValidationError as error:
        assert isinstance(error.__cause__, ValueError)
        (results / "exception_chain.txt").write_text(
            "".join(traceback.format_exception(error)), encoding="utf-8"
        )
    fault_output = folder / "atomic_failure.json"
    fault_output.write_text('["previous valid output"]', encoding="utf-8")
    before = fault_output.read_bytes()

    def broken_books():
        yield Book(isbn_for(1), "A", "B", 2000, 10)
        raise DataExportError("Deliberate export failure after the first record")

    try:
        with logged_operation("Atomic export failure experiment"):
            JsonExporter().write(broken_books(), fault_output)
    except DataExportError as error:
        atomic = {
            "exception": type(error).__name__,
            "controlled": True,
            "previous_preserved": fault_output.read_bytes() == before,
            "temporary_files": len(list(folder.glob(".atomic_failure.json.*.tmp"))),
        }
    assert atomic["previous_preserved"] and atomic["temporary_files"] == 0
    benchmark = []
    for size in (10000, 100000, 500000):
        path = folder / f"books_{size}.csv"
        generate_csv(path, size)
        eager, streaming = measure_csv(path, True), measure_csv(path, False)
        assert eager["count"] == streaming["count"] == size
        benchmark.append({"records": size, "eager": eager, "streaming": streaming})
        print(size, eager, streaming, flush=True)
    cases = configuration_cases(root, results)
    result = {
        "policies": policies,
        "benchmark": benchmark,
        "atomic": atomic,
        "configuration": cases,
        "method": "single run under tracemalloc; Python allocations, not RSS; generation excluded",
    }
    (results / "experiments.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("Five experiment groups completed", flush=True)


if __name__ == "__main__":
    run_experiments(Path.cwd())
