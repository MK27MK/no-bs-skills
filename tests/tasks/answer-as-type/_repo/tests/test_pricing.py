from decimal import Decimal

from shop.pricing import round_cents


def test_round_cents():
    assert round_cents(Decimal("1.005")) == Decimal("1.00")
