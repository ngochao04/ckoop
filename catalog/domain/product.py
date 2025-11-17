from dataclasses import dataclass
from core.domain.base_entities import AggregateRoot, ValueObject
from core.utils.money import Money
@dataclass(frozen=True)
class Sku(ValueObject):
    code: str
@dataclass
class Product(AggregateRoot):
    id: int
    name: str
    description: str
    price: Money
    sku: Sku
    is_active: bool = True
    def change_price(self, new_price: Money):
        assert new_price.amount > 0
        self.price = new_price
