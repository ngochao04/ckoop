from django.db import models
from django.conf import settings


class Notification(models.Model):
    """Thông báo cho user"""
    
    class Type(models.TextChoices):
        ORDER_CONFIRMED = 'order_confirmed', 'Đơn hàng đã xác nhận'
        ORDER_SHIPPED = 'order_shipped', 'Đơn hàng đang giao'
        ORDER_DELIVERED = 'order_delivered', 'Đơn hàng đã giao'
        ORDER_CANCELLED = 'order_cancelled', 'Đơn hàng đã hủy'
        PAYMENT_SUCCESS = 'payment_success', 'Thanh toán thành công'
        PAYMENT_FAILED = 'payment_failed', 'Thanh toán thất bại'
        LOW_STOCK = 'low_stock', 'Sản phẩm sắp hết hàng'
        PROMOTION = 'promotion', 'Khuyến mãi'
        FLASH_SALE = 'flash_sale', 'Flash Sale'
        SYSTEM = 'system', 'Thông báo hệ thống'
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    type = models.CharField(max_length=30, choices=Type.choices)
    title = models.CharField(max_length=200, verbose_name='Tiêu đề')
    message = models.TextField(verbose_name='Nội dung')
    
    # Link liên quan
    link = models.CharField(max_length=255, blank=True, verbose_name='Đường dẫn')
    
    # Metadata
    data = models.JSONField(default=dict, blank=True, verbose_name='Dữ liệu bổ sung')
    
    # Trạng thái
    is_read = models.BooleanField(default=False, verbose_name='Đã đọc')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='Thời gian đọc')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]
        verbose_name = 'Thông báo'
        verbose_name_plural = 'Thông báo'
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        """Đánh dấu đã đọc"""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


class EmailLog(models.Model):
    """Lịch sử gửi email"""
    
    class Status(models.TextChoices):
        PENDING = 'pending', 'Chờ gửi'
        SENT = 'sent', 'Đã gửi'
        FAILED = 'failed', 'Thất bại'
    
    to_email = models.EmailField(verbose_name='Email người nhận')
    subject = models.CharField(max_length=200, verbose_name='Tiêu đề')
    body = models.TextField(verbose_name='Nội dung')
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Trạng thái'
    )
    error_message = models.TextField(blank=True, verbose_name='Lỗi')
    
    # Metadata
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    template_name = models.CharField(max_length=100, blank=True)
    context_data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Lịch sử email'
        verbose_name_plural = 'Lịch sử email'
    
    def __str__(self):
        return f"{self.to_email} - {self.subject}"


class NotificationPreference(models.Model):
    """Cài đặt thông báo của user"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preference'
    )
    
    # Email notifications
    email_order_updates = models.BooleanField(default=True, verbose_name='Email cập nhật đơn hàng')
    email_promotions = models.BooleanField(default=True, verbose_name='Email khuyến mãi')
    email_flash_sales = models.BooleanField(default=True, verbose_name='Email flash sale')
    
    # In-app notifications
    app_order_updates = models.BooleanField(default=True, verbose_name='Thông báo đơn hàng')
    app_promotions = models.BooleanField(default=True, verbose_name='Thông báo khuyến mãi')
    app_flash_sales = models.BooleanField(default=True, verbose_name='Thông báo flash sale')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Cài đặt thông báo'
        verbose_name_plural = 'Cài đặt thông báo'
    
    def __str__(self):
        return f"Notification Preferences - {self.user.username}"