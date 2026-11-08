"""Domain-specific exception hierarchy retaining useful record context."""


class ApplicationError(Exception):
    """Expected application failure."""


class ConfigurationError(ApplicationError):
    """Invalid configuration or startup resource."""


class DataError(ApplicationError):
    """Base data operation error."""


class DataImportError(DataError):
    """An input file cannot be read or parsed structurally."""


class DataValidationError(DataError):
    """A record violates its contract."""


class RecordValidationError(DataValidationError):
    def __init__(
        self, message: str, *, line_number: int | None = None, field: str | None = None
    ) -> None:
        super().__init__(message)
        self.line_number = line_number
        self.field = field


class DataExportError(DataError):
    """Output could not be committed."""
