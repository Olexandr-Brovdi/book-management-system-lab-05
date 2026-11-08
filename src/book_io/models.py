"""Typed internal data separated from file mappings."""

from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Book:
    isbn: str
    title: str
    author: str
    year: int
    pages: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SourceRow:
    line: int
    data: object
    error: str | None = None


@dataclass(frozen=True, slots=True)
class ProcessingConfig:
    min_year: int
    max_year: int
    skip_invalid: bool


@dataclass(frozen=True, slots=True)
class LoggingConfig:
    level: str
    path: Path
    max_bytes: int = 1_000_000
    backups: int = 2


@dataclass(frozen=True, slots=True)
class AppConfig:
    input_path: Path
    output_path: Path
    input_format: str
    output_format: str
    processing: ProcessingConfig
    logging: LoggingConfig
    summary_path: Path


@dataclass
class ImportStatistics:
    total: int = 0
    valid: int = 0
    invalid: int = 0
    exported: int = 0
