"""Safe YAML loading, exact types, relative path resolution and fail-fast checks."""

from datetime import date
from pathlib import Path

import yaml

from book_io.exceptions import ConfigurationError
from book_io.models import AppConfig, LoggingConfig, ProcessingConfig


def load_config(path: Path) -> AppConfig:
    try:
        with path.open(encoding="utf-8-sig") as handle:
            raw = yaml.safe_load(handle)
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise ConfigurationError("Cannot read valid YAML configuration") from error
    try:
        if (
            not isinstance(raw, dict)
            or type(raw.get("schema_version")) is not int
            or raw.get("schema_version") != 1
        ):
            raise ValueError("schema_version must be 1")
        incoming, outgoing = raw["input"], raw["output"]
        processing, logs = raw["processing"], raw["logging"]
        if not all(
            isinstance(value, dict) for value in (incoming, outgoing, processing, logs)
        ):
            raise TypeError("Configuration sections must be mappings")
        minimum, maximum = processing["min_year"], processing["max_year"]
        skip = processing["skip_invalid"]
        if (
            type(minimum) is not int
            or type(maximum) is not int
            or type(skip) is not bool
        ):
            raise TypeError(
                "Years must be integers and skip_invalid must be YAML boolean"
            )
        if not 1 <= minimum <= maximum <= date.today().year:
            raise ValueError("Invalid permitted year range")

        def resolve(value: object) -> Path:
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Path must be nonempty text")
            return (path.resolve().parent / Path(value)).resolve()

        input_path, output_path = resolve(incoming["path"]), resolve(outgoing["path"])
        input_format = incoming.get("format", "auto")
        output_format = outgoing.get("format", "auto")
        if input_format == "auto":
            input_format = input_path.suffix.lstrip(".").lower()
        if output_format == "auto":
            output_format = output_path.suffix.lstrip(".").lower()
        if input_format not in ("csv", "jsonl") or output_format not in (
            "json",
            "jsonl",
        ):
            raise ValueError("Unsupported input/output format")
        level = logs["level"]
        if level not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            raise ValueError("Unsupported logging level")
        max_bytes, backups = logs.get("max_bytes", 1000000), logs.get("backups", 2)
        if (
            type(max_bytes) is not int
            or max_bytes < 1
            or type(backups) is not int
            or backups < 1
        ):
            raise ValueError("Invalid log rotation parameters")
        log_path = resolve(logs["path"])
        summary = resolve(
            outgoing.get("summary", str(output_path.with_suffix(".summary.json")))
        )
        config = AppConfig(
            input_path,
            output_path,
            input_format,
            output_format,
            ProcessingConfig(minimum, maximum, skip),
            LoggingConfig(level, log_path, max_bytes, backups),
            summary,
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ConfigurationError(
            "Configuration structure or values are invalid"
        ) from error
    validate_config(config, path)
    return config


def validate_config(config: AppConfig, source: Path | None = None) -> None:
    paths = [
        config.input_path,
        config.output_path,
        config.summary_path,
        config.logging.path,
    ]
    if source is not None:
        paths.append(source.resolve())
    if len({p.resolve() for p in paths}) != len(paths):
        raise ConfigurationError(
            "Input, output, summary, log and config paths must differ"
        )
    if not config.input_path.is_file():
        raise ConfigurationError("Input file is missing or is not a regular file")
    for target in (config.output_path, config.summary_path, config.logging.path):
        if target.exists() and not target.is_file():
            raise ConfigurationError("An output destination is not a regular file")
