def format_price(amount: float, currency: str = "EUR") -> str:
    return f"{amount} {currency}"


def apply_discount(amount: float, percent: float) -> float:
    return amount - amount * percent / 100
