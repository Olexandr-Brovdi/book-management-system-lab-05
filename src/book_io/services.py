"""Reliability policy, statistics and application orchestration."""

import json
import logging
from collections.abc import Iterator
from contextlib import closing
from dataclasses import asdict
from pathlib import Path

from book_io.exceptions import RecordValidationError
from book_io.exporters import select_exporter
from book_io.models import AppConfig, Book, ImportStatistics, ProcessingConfig
from book_io.readers import Importer, select_importer
from book_io.resources import atomic_text, logged_operation
from book_io.validators import parse_book

logger = logging.getLogger(__name__)


def import_books(
    path: Path,
    importer: Importer,
    policy: ProcessingConfig,
    statistics: ImportStatistics,
) -> Iterator[Book]:
    with closing(importer.read(path)) as rows:
        for source in rows:
            statistics.total += 1
            try:
                book = parse_book(source, policy)
            except RecordValidationError as error:
                statistics.invalid += 1
                logger.warning(
                    "Invalid record line=%s field=%s reason=%s",
                    error.line_number,
                    error.field,
                    error,
                )
                if policy.skip_invalid:
                    continue
                raise
            else:
                statistics.valid += 1
                yield book


def process(
    config: AppConfig, statistics: ImportStatistics | None = None
) -> ImportStatistics:
    stats = statistics if statistics is not None else ImportStatistics()
    with logged_operation("Book import/export"):
        with closing(
            import_books(
                config.input_path,
                select_importer(config.input_format),
                config.processing,
                stats,
            )
        ) as books:
            committed = select_exporter(config.output_format).write(
                books, config.output_path
            )
        stats.exported = committed
        with atomic_text(config.summary_path) as handle:
            json.dump(asdict(stats), handle, indent=2)
    logger.info(
        "Total=%s valid=%s invalid=%s exported=%s",
        stats.total,
        stats.valid,
        stats.invalid,
        stats.exported,
    )
    return stats
