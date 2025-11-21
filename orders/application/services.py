from dataclasses import dataclass
from typing import Optional
from cart.infrastructure.models import CartModel
from orders.infrastructure.models import OrderModel, OrderLineModel
from catalog.infrastructure.models import ProductModel, InventoryLog
from accounts.infrastructure.models import Address
from promotions.models import Voucher, VoucherUsage

@dataclass
class CheckoutInput:
    user_id: int
    address_id: Optional[int] = None
    payment_method: str = 'cod'
    voucher_code: Optional[str] = None

class OrderService:
    def checkout(self, data: CheckoutInput) -> int:
        cart = CartModel.objects.filter(owner_id=data.user_id).prefetch_related('items__product').first()
        if not cart or not cart.items.exists():
            raise ValueError('Giỏ hàng trống')
        
        # Kiểm tra tồn kho trước
        for it in cart.items.all():
            product = it.product
            if product.stock_quantity < it.qty:
                raise ValueError(f'Sản phẩm {product.name} chỉ còn {product.stock_quantity} {product.unit}')
        
        # Tính tổng đơn hàng
        total = 0
        for it in cart.items.all():
            line_total = it.product.price_vnd * it.qty
            total += line_total
        
        # Áp dụng voucher nếu có
        discount_amount = 0
        voucher = None
        if data.voucher_code:
            try:
                voucher = Voucher.objects.get(code=data.voucher_code.upper())
                can_use, message = voucher.can_use(cart.owner, total)
                if can_use:
                    discount_amount = voucher.calculate_discount(total)
                    total = total - discount_amount
            except Voucher.DoesNotExist:
                pass  # Bỏ qua nếu voucher không tồn tại
        
        # Lấy địa chỉ giao hàng
        delivery_address = None
        if data.address_id:
            try:
                delivery_address = Address.objects.get(id=data.address_id, user_id=data.user_id)
            except Address.DoesNotExist:
                raise ValueError('Địa chỉ giao hàng không hợp lệ')
        
        # Tạo đơn hàng
        order = OrderModel.objects.create(
            buyer_id=data.user_id,
            total_vnd=total,
            delivery_address=delivery_address
        )
        
        # Tạo order lines
        for it in cart.items.all():
            line_total = it.product.price_vnd * it.qty
            
            OrderLineModel.objects.create(
                order=order,
                product=it.product,
                product_name=it.product.name,
                sku=it.product.sku,
                price_vnd=it.product.price_vnd,
                qty=it.qty,
                line_total=line_total
            )
            
            # Giảm tồn kho
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
        
        # Lưu voucher usage nếu có
        if voucher and discount_amount > 0:
            VoucherUsage.objects.create(
                voucher=voucher,
                user=cart.owner,
                order=order,
                discount_amount=discount_amount
            )
            
            # Tăng used_quantity
            voucher.used_quantity += 1
            voucher.save()
        
        # Tạo payment
        from payments.models import Payment
        Payment.objects.create(
            order=order,
            method=data.payment_method,
            amount=total,
            status='pending'
        )
        
        # Xóa giỏ hàng
        cart.items.all().delete()
        
        return order.id