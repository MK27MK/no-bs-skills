from pathlib import Path
from typing import NamedTuple


class Row(NamedTuple):
    name: str
    email: str
    age: int


def parse_line(line: str) -> Row:
    # fields are separated by ';', surrounding spaces are noise, age may be empty -> 0
    ...


def load(path: Path) -> list[Row]:
    # skip the header line and blank lines, lines starting with '#' are comments
    ...
