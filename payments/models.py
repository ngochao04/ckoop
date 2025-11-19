from django.db import models
from django.conf import settings


class Payment(models.Model):
    """Thông tin thanh toán đơn hàng"""
    
    class Method(models.TextChoices):
        COD = 'cod', 'Thanh toán khi nhận hàng (COD)'
        BANK_TRANSFER = 'bank', 'Chuyển khoản ngân hàng'
        MOMO = 'momo', 'Ví MoMo'
        VNPAY = 'vnpay', 'VNPay'
        ZALOPAY = 'zalopay', 'ZaloPay'
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Chờ thanh toán'
        PAID = 'paid', 'Đã thanh toán'
        FAILED = 'failed', 'Thất bại'
        REFUNDED = 'refunded', 'Đã hoàn tiền'
        CANCELLED = 'cancelled', 'Đã hủy'
    
    order = models.OneToOneField(
        'orders.OrderModel', 
        on_delete=models.CASCADE, 
        related_name='payment'
    )
    method = models.CharField(
        max_length=20, 
        choices=Method.choices,
        verbose_name='Phương thức thanh toán'
    )
    status = models.CharField(
        max_length=20, 
        choices=Status.choices, 
        default=Status.PENDING,
        verbose_name='Trạng thái'
    )
    amount = models.PositiveIntegerField(verbose_name='Số tiền (VND)')
    
    # Gateway transaction info
    transaction_id = models.CharField(max_length=100, blank=True, verbose_name='Mã giao dịch')
    gateway_response = models.JSONField(default=dict, blank=True, verbose_name='Phản hồi từ gateway')
    
    # Timestamps
    payment_date = models.DateTimeField(null=True, blank=True, verbose_name='Ngày thanh toán')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Thanh toán'
        verbose_name_plural = 'Thanh toán'
    
    def __str__(self):
        return f"Payment #{self.id} - Order #{self.order_id} - {self.get_method_display()}"
    
    def mark_as_paid(self, transaction_id='', gateway_response=None):
        """Đánh dấu đã thanh toán"""
        from django.utils import timezone
        self.status = self.Status.PAID
        self.payment_date = timezone.now()
        self.transaction_id = transaction_id
        if gateway_response:
            self.gateway_response = gateway_response
        self.save()
        
        # Cập nhật trạng thái order
        self.order.status = 'paid'
        self.order.save()


class BankAccount(models.Model):
    """Tài khoản ngân hàng để nhận chuyển khoản"""
    
    bank_name = models.CharField(max_length=100, verbose_name='Tên ngân hàng')
    bank_code = models.CharField(max_length=20, verbose_name='Mã ngân hàng')
    account_number = models.CharField(max_length=50, verbose_name='Số tài khoản')
    account_holder = models.CharField(max_length=100, verbose_name='Chủ tài khoản')
    branch = models.CharField(max_length=100, blank=True, verbose_name='Chi nhánh')
    qr_code = models.ImageField(upload_to='bank_qr/', blank=True, verbose_name='Mã QR')
    is_active = models.BooleanField(default=True, verbose_name='Đang hoạt động')
    display_order = models.PositiveIntegerField(default=0, verbose_name='Thứ tự hiển thị')
    
    class Meta:
        ordering = ['display_order', 'bank_name']
        verbose_name = 'Tài khoản ngân hàng'
        verbose_name_plural = 'Tài khoản ngân hàng'
    
    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"


class PaymentGatewayConfig(models.Model):
    """Cấu hình các cổng thanh toán"""
    
    name = models.CharField(max_length=50, unique=True, verbose_name='Tên gateway')
    display_name = models.CharField(max_length=100, verbose_name='Tên hiển thị')
    logo = models.ImageField(upload_to='payment_gateways/', blank=True, verbose_name='Logo')
    is_active = models.BooleanField(default=False, verbose_name='Đang hoạt động')
    config = models.JSONField(default=dict, verbose_name='Cấu hình')
    
    # Fees
    fixed_fee = models.PositiveIntegerField(default=0, verbose_name='Phí cố định (VND)')
    percentage_fee = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        verbose_name='Phí % (2.5 = 2.5%)'
    )
    
    class Meta:
        verbose_name = 'Cấu hình cổng thanh toán'
        verbose_name_plural = 'Cấu hình cổng thanh toán'
    
    def __str__(self):
        return self.display_name