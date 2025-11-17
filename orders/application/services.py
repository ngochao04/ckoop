from dataclasses import dataclass
from cart.infrastructure.models import CartModel
from orders.infrastructure.models import OrderModel, OrderLineModel
@dataclass
class CheckoutInput:
    user_id: int
class OrderService:
    def checkout(self, data: CheckoutInput) -> int:
        cart = CartModel.objects.filter(owner_id=data.user_id).prefetch_related('items__product').first()
        if not cart or not cart.items.exists():
            raise ValueError('Giỏ hàng trống')
        total = 0
        order = OrderModel.objects.create(buyer_id=data.user_id, total_vnd=0)
        for it in cart.items.all():
            line_total = it.product.price_vnd * it.qty
            total += line_total
            OrderLineModel.objects.create(
                order=order, product_name=it.product.name, sku=it.product.sku,
                price_vnd=it.product.price_vnd, qty=it.qty
            )
        order.total_vnd = total
        order.save()
        cart.items.all().delete()
        return order.id
