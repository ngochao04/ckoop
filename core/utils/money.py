from dataclasses import dataclass
@dataclass(frozen=True)
class Money:
    amount: int
    currency: str = 'VND'
    def add(self, other:'Money')->'Money':
        assert self.currency == other.currency
        return Money(self.amount + other.amount, self.currency)
    def mul(self, qty:int)->'Money':
        return Money(self.amount * qty, self.currency)
