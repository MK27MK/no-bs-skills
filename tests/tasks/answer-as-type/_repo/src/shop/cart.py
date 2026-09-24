from decimal import Decimal

from shop.pricing import discount, round_cents, with_vat


class Cart:
    def __init__(self) -> None:
        self.items: list[tuple[str, Decimal]] = []

    def add(self, sku: str, price: Decimal) -> None:
        self.items.append((sku, price))

    def total(self, percent_off: int = 0) -> Decimal:
        net = sum((price for _, price in self.items), Decimal(0))
        return round_cents(with_vat(discount(net, percent_off)))
