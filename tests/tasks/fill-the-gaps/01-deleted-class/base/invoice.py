from dataclasses import dataclass
from decimal import Decimal

from money import Money


@dataclass
class Line:
    description: str
    unit_price: Decimal
    quantity: int


def total(lines: list[Line]) -> Money:
    result = Money(0)
    for line in lines:
        result = result + Money(line.unit_price * line.quantity)
    return result
