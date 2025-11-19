from dataclasses import dataclass
from cart.infrastructure.models import CartModel
from orders.infrastructure.models import OrderModel, OrderLineModel
from catalog.infrastructure.models import ProductModel, InventoryLog  # ← THÊM

@dataclass
class CheckoutInput:
    user_id: int

class OrderService:
    def checkout(self, data: CheckoutInput) -> int:
        cart = CartModel.objects.filter(owner_id=data.user_id).prefetch_related('items__product').first()
        if not cart or not cart.items.exists():
            raise ValueError('Giỏ hàng trống')
        
        # ← THÊM: Kiểm tra tồn kho trước
        for it in cart.items.all():
            product = it.product
            if product.stock_quantity < it.qty:
                raise ValueError(f'Sản phẩm {product.name} chỉ còn {product.stock_quantity} {product.unit}')
        
        total = 0
        order = OrderModel.objects.create(buyer_id=data.user_id, total_vnd=0)
        
        for it in cart.items.all():
            line_total = it.product.price_vnd * it.qty
            total += line_total
            
            OrderLineModel.objects.create(
                order=order, 
                product_name=it.product.name, 
                sku=it.product.sku,
                price_vnd=it.product.price_vnd, 
                qty=it.qty
            )
            
            # ← THÊM: Giảm tồn kho
            product = it.product
            previous_stock = product.stock_quantity
            product.reduce_stock(it.qty)
            
            # Ghi log inventory
            InventoryLog.objects.create(
                product=product,
                action='out',
                quantity=it.qty,
                previous_stock=previous_stock,
                new_stock=product.stock_quantity,
                note=f'Xuất kho cho đơn hàng #{order.id}',
                order=order
            )
        
        order.total_vnd = total
        order.save()
        cart.items.all().delete()
        return order.id