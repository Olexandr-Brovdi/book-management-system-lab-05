"""Reproducible CSV fixtures, including valid ISBN-13 check digits."""

import csv
from pathlib import Path

from book_io.validators import FIELDS


def isbn_for(number: int) -> str:
    prefix = "978" + f"{number:09d}"
    checksum = (
        -sum(int(x) * (1 if i % 2 == 0 else 3) for i, x in enumerate(prefix))
    ) % 10
    return prefix + str(checksum)


def generate_csv(path: Path, count: int, invalid: int = 0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(FIELDS)
        for i in range(count):
            writer.writerow(
                (
                    isbn_for(i),
                    f"Книга {i}",
                    f"Автор {i % 10}",
                    1900 + i % 126,
                    80 + i % 921,
                )
            )
        for i in range(invalid):
            writer.writerow(
                (isbn_for(count + i), "Некоректний запис", "Автор", 2000, "wrong")
            )
