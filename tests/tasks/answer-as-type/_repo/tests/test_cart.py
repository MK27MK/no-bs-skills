from decimal import Decimal

from shop.cart import Cart


def test_total_adds_vat():
    cart = Cart()
    cart.add("A1", Decimal("10"))
    assert cart.total() == Decimal("12.20")


def test_total_with_discount():
    cart = Cart()
    cart.add("A1", Decimal("100"))
    assert cart.total(percent_off=10) == Decimal("109.80")
