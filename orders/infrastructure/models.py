from django.db import models
from django.conf import settings

class OrderModel(models.Model):
    class Status(models.TextChoices):
        NEW = 'new','Mới'
        WAIT = 'wait', 'Chờ Thanh toán'
        PAID = 'paid','Trả'
        SHIP = 'ship','Giao Hàng'
        DONE = 'done','Hoàn Thành'
        CANCEL = 'cancel','Đã Hủy'
    
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    total_vnd = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.NEW)
    
    # ✅ SỬA: Địa chỉ giao hàng
    delivery_address = models.ForeignKey(
        'accounts.ShippingAddress',  # ✅ ĐỔI từ Address thành ShippingAddress
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.id} - {self.buyer.username}"


class OrderLineModel(models.Model):
    order = models.ForeignKey(OrderModel, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('catalog.ProductModel', on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=180)
    sku = models.CharField(max_length=64)
    price_vnd = models.PositiveIntegerField()
    qty = models.PositiveIntegerField()
    line_total = models.PositiveIntegerField(default=0)
    
    def save(self, *args, **kwargs):
        if not self.line_total:
            self.line_total = self.price_vnd * self.qty
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.product_name} x {self.qty}"