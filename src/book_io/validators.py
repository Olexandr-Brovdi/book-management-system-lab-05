"""Book boundary validation including ISBN-10/13 check digits."""

from book_io.exceptions import RecordValidationError
from book_io.models import Book, ProcessingConfig, SourceRow

FIELDS = ("isbn", "title", "author", "year", "pages")


def valid_isbn(value: str) -> bool:
    if (
        len(value) == 13
        and value.isascii()
        and value.isdigit()
        and value[:3] in ("978", "979")
    ):
        return (
            sum(int(digit) * (1 if i % 2 == 0 else 3) for i, digit in enumerate(value))
            % 10
            == 0
        )
    if (
        len(value) == 10
        and value[:9].isascii()
        and value[:9].isdigit()
        and (value[-1].isdigit() and value[-1].isascii() or value[-1] == "X")
    ):
        digits = [int(x) for x in value[:9]] + [
            10 if value[-1] == "X" else int(value[-1])
        ]
        return sum((10 - i) * digit for i, digit in enumerate(digits)) % 11 == 0
    return False


def parse_book(source: SourceRow, config: ProcessingConfig) -> Book:
    if source.error is not None:
        raise RecordValidationError(source.error, line_number=source.line, field="json")
    row = source.data
    if not isinstance(row, dict) or set(row) != set(FIELDS):
        raise RecordValidationError(
            "Record columns do not match schema",
            line_number=source.line,
            field="schema",
        )
    text: dict[str, str] = {}
    for field in ("isbn", "title", "author"):
        value = row[field]
        if not isinstance(value, str) or not value.strip():
            raise RecordValidationError(
                "Required text is empty", line_number=source.line, field=field
            )
        text[field] = " ".join(value.split())
    isbn = text["isbn"].replace("-", "").replace(" ", "").upper()
    if not valid_isbn(isbn):
        raise RecordValidationError(
            "ISBN length or check digit is invalid",
            line_number=source.line,
            field="isbn",
        )
    numbers: dict[str, int] = {}
    for field in ("year", "pages"):
        value = row[field]
        try:
            if type(value) is int:
                numbers[field] = value
            elif isinstance(value, str):
                numbers[field] = int(value.strip())
            else:
                raise TypeError("Expected integer value")
        except (TypeError, ValueError) as error:
            raise RecordValidationError(
                "Field must be an integer", line_number=source.line, field=field
            ) from error
    if not config.min_year <= numbers["year"] <= config.max_year:
        raise RecordValidationError(
            "Year is outside the configured range",
            line_number=source.line,
            field="year",
        )
    if numbers["pages"] <= 0:
        raise RecordValidationError(
            "Pages must be positive", line_number=source.line, field="pages"
        )
    return Book(isbn, text["title"], text["author"], numbers["year"], numbers["pages"])
