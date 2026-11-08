"""Own context managers for atomic text output and logged operation lifecycle."""

import logging
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from time import perf_counter
from typing import TextIO

from book_io.exceptions import ApplicationError, DataExportError

logger = logging.getLogger(__name__)


@contextmanager
def atomic_text(path: Path) -> Iterator[TextIO]:
    temporary: Path | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            prefix="." + path.name + ".",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            yield handle
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except OSError as error:
        raise DataExportError("Cannot commit atomic output") from error
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                logger.error("Could not remove temporary output")


@contextmanager
def logged_operation(name: str) -> Iterator[None]:
    start = perf_counter()
    logger.info("%s started", name)
    try:
        yield
    except ApplicationError:
        logger.exception("%s failed", name)
        raise
    else:
        logger.info("%s finished", name)
    finally:
        logger.debug("%s elapsed=%.6f s", name, perf_counter() - start)
