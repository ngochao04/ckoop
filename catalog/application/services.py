from dataclasses import dataclass
from typing import Iterable
from core.utils.money import Money
from catalog.domain.product import Product, Sku
from catalog.infrastructure.repositories import ProductRepository
@dataclass
class CreateProductInput:
    name: str
    description: str
    price_vnd: int
    sku: str
class ProductService:
    def __init__(self, repo: ProductRepository):
        self.repo = repo
    def create_product(self, data: CreateProductInput) -> Product:
        entity = Product(
            id=0, name=data.name, description=data.description,
            price=Money(data.price_vnd), sku=Sku(data.sku), is_active=True
        )
        return self.repo.save(entity)
    def list_products(self) -> Iterable[Product]:
        return self.repo.list_active()
