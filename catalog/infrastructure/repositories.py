from typing import Optional, Iterable
from .models import ProductModel
from catalog.domain.product import Product, Sku
from core.utils.money import Money
class ProductRepository:
    def to_domain(self, m: ProductModel) -> Product:
        return Product(
            id=m.id, name=m.name, description=m.description,
            price=Money(m.price_vnd), sku=Sku(m.sku), is_active=m.is_active,
        )
    def get_by_id(self, pid: int) -> Optional[Product]:
        m = ProductModel.objects.filter(id=pid).first()
        return self.to_domain(m) if m else None
    def list_active(self) -> Iterable[Product]:
        for m in ProductModel.objects.filter(is_active=True).order_by('-id'):
            yield self.to_domain(m)
    def save(self, e: Product) -> Product:
        if e.id:
            m = ProductModel.objects.get(id=e.id)
            m.name, m.description = e.name, e.description
            m.price_vnd = e.price.amount
            m.is_active = e.is_active
            m.save()
            return self.to_domain(m)
        m = ProductModel.objects.create(
            name=e.name, description=e.description,
            price_vnd=e.price.amount, sku=e.sku.code, is_active=e.is_active
        )
        return self.to_domain(m)
