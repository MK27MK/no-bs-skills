from decimal import Decimal


class Money:
    def __init__(self, amount):
        self.amount = Decimal(amount)

    def __add__(self, other):
        return Money(self.amount + other.amount)
