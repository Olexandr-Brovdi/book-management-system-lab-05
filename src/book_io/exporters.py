"""Streaming serialization without constructing a full catalogue list."""

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Protocol

from book_io.exceptions import DataExportError
from book_io.models import Book
from book_io.resources import atomic_text


class Exporter(Protocol):
    def write(self, books: Iterable[Book], path: Path) -> int: ...


class JsonExporter:
    def write(self, books: Iterable[Book], path: Path) -> int:
        count = 0
        try:
            with atomic_text(path) as handle:
                handle.write("[\n")
                for book in books:
                    if count:
                        handle.write(",\n")
                    json.dump(
                        book.to_dict(), handle, ensure_ascii=False, allow_nan=False
                    )
                    count += 1
                handle.write("\n]\n")
        except (TypeError, ValueError, UnicodeError) as error:
            raise DataExportError("Cannot serialize book data") from error
        return count


class JsonLinesExporter:
    def write(self, books: Iterable[Book], path: Path) -> int:
        count = 0
        try:
            with atomic_text(path) as handle:
                for book in books:
                    handle.write(
                        json.dumps(book.to_dict(), ensure_ascii=False, allow_nan=False)
                        + "\n"
                    )
                    count += 1
        except (TypeError, ValueError, UnicodeError) as error:
            raise DataExportError("Cannot serialize JSON Lines") from error
        return count


def select_exporter(format_name: str) -> Exporter:
    if format_name == "json":
        return JsonExporter()
    if format_name == "jsonl":
        return JsonLinesExporter()
    raise DataExportError("Unsupported output format")
