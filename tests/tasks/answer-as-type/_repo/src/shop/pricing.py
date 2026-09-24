from decimal import Decimal

VAT = Decimal("0.22")


def with_vat(amount: Decimal) -> Decimal:
    """Gross amount for a net amount."""
    return amount * (1 + VAT)


def discount(amount: Decimal, percent: int) -> Decimal:
    return amount * (100 - percent) / 100


def round_cents(amount: Decimal) -> Decimal:
    """Round to two decimals."""
    return amount.quantize(Decimal("0.01"))


def legacy_price(amount: float) -> float:
    return round(amount * 1.22, 2)
