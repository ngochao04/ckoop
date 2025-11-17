from django.db import models
from django.conf import settings
class OrderModel(models.Model):
    class Status(models.TextChoices):
        NEW = 'new','New'
        PAID = 'paid','Paid'
        SHIP = 'ship','Shipping'
        DONE = 'done','Completed'
        CANCEL = 'cancel','Cancelled'
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    total_vnd = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField(auto_now_add=True)
class OrderLineModel(models.Model):
    order = models.ForeignKey(OrderModel, on_delete=models.CASCADE, related_name='lines')
    product_name = models.CharField(max_length=180)
    sku = models.CharField(max_length=64)
    price_vnd = models.PositiveIntegerField()
    qty = models.PositiveIntegerField()
