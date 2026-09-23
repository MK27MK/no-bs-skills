from dataclasses import dataclass
from decimal import Decimal

from money import Money


@dataclass
class Line:
    description: str
    unit_price: Decimal
    quantity: int


def total(lines: list[Line]) -> Decimal:
    ...


def total_with_vat(lines: list[Line], vat_rate: Decimal) -> Decimal:
    ...
