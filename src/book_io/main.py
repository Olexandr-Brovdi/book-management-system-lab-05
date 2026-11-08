"""Controlled application exit for expected configuration and data errors."""

import argparse
import json
import logging
from dataclasses import asdict
from pathlib import Path

from book_io.config import load_config
from book_io.exceptions import ApplicationError
from book_io.logging_config import configure_logging
from book_io.services import process


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Lab_05 Варіант 2 — імпорт та експорт книг"
    )
    parser.add_argument("--config", type=Path, default=Path("config.yaml"))
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        configure_logging(config.logging)
        statistics = process(config)
    except ApplicationError as error:
        logging.getLogger("book_io").error("Application error: %s", error)
        raise SystemExit(1) from error
    else:
        print(json.dumps(asdict(statistics), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
