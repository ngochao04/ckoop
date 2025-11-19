from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


class Voucher(models.Model):
    """Mã giảm giá"""
    
    class DiscountType(models.TextChoices):
        PERCENTAGE = 'percentage', 'Giảm theo %'
        FIXED = 'fixed', 'Giảm cố định'
        FREE_SHIP = 'free_ship', 'Miễn phí vận chuyển'
    
    code = models.CharField(max_length=50, unique=True, verbose_name='Mã voucher')
    name = models.CharField(max_length=200, verbose_name='Tên chương trình')
    description = models.TextField(blank=True, verbose_name='Mô tả')
    
    discount_type = models.CharField(
        max_length=20, 
        choices=DiscountType.choices,
        verbose_name='Loại giảm giá'
    )
    discount_value = models.PositiveIntegerField(
        verbose_name='Giá trị giảm (% hoặc VND)',
        help_text='Với % thì nhập 10 = 10%, với cố định thì nhập số tiền VND'
    )
    max_discount = models.PositiveIntegerField(
        default=0,
        verbose_name='Giảm tối đa (VND)',
        help_text='Chỉ áp dụng cho giảm theo %. 0 = không giới hạn'
    )
    
    # Điều kiện áp dụng
    min_order_value = models.PositiveIntegerField(
        default=0,
        verbose_name='Giá trị đơn hàng tối thiểu (VND)'
    )
    
    # Số lượng
    total_quantity = models.PositiveIntegerField(
        default=0,
        verbose_name='Tổng số lượng',
        help_text='0 = không giới hạn'
    )
    used_quantity = models.PositiveIntegerField(
        default=0,
        verbose_name='Đã sử dụng'
    )
    usage_limit_per_user = models.PositiveIntegerField(
        default=1,
        verbose_name='Giới hạn sử dụng mỗi user',
        help_text='0 = không giới hạn'
    )
    
    # Thời gian
    start_date = models.DateTimeField(verbose_name='Ngày bắt đầu')
    end_date = models.DateTimeField(verbose_name='Ngày kết thúc')
    
    # Cài đặt
    is_active = models.BooleanField(default=True, verbose_name='Đang hoạt động')
    is_public = models.BooleanField(
        default=True,
        verbose_name='Công khai',
        help_text='Voucher công khai sẽ hiển thị cho tất cả user'
    )
    
    # Giới hạn sản phẩm/danh mục
    applicable_products = models.ManyToManyField(
        'catalog.ProductModel',
        blank=True,
        verbose_name='Áp dụng cho sản phẩm',
        help_text='Để trống = áp dụng cho tất cả'
    )
    applicable_categories = models.ManyToManyField(
        'catalog.Category',
        blank=True,
        verbose_name='Áp dụng cho danh mục',
        help_text='Để trống = áp dụng cho tất cả'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Voucher'
        verbose_name_plural = 'Voucher'
    
    def __str__(self):
        return "{} - {}".format(self.code, self.name)
    
    def clean(self):
        if self.start_date >= self.end_date:
            raise ValidationError('Ngày kết thúc phải sau ngày bắt đầu')
        
        if self.discount_type == self.DiscountType.PERCENTAGE:
            if self.discount_value > 100:
                raise ValidationError('Giảm giá % không được vượt quá 100%')
    
    def is_valid(self):
        """Kiểm tra voucher còn hợp lệ không"""
        now = timezone.now()
        
        if not self.is_active:
            return False, "Voucher không còn hoạt động"
        
        if now < self.start_date:
            return False, "Voucher chưa đến thời gian sử dụng"
        
        if now > self.end_date:
            return False, "Voucher đã hết hạn"
        
        if self.total_quantity > 0 and self.used_quantity >= self.total_quantity:
            return False, "Voucher đã hết lượt sử dụng"
        
        return True, "OK"
    
    def can_use(self, user, order_value):
        """Kiểm tra user có thể sử dụng voucher này không"""
        is_valid, message = self.is_valid()
        if not is_valid:
            return False, message
        
        # Kiểm tra giá trị đơn hàng tối thiểu
        if order_value < self.min_order_value:
            # FIX: Sử dụng format() thay vì f-string với :, để tránh lỗi
            return False, "Đơn hàng tối thiểu {:,}đ".format(self.min_order_value)
        
        # Kiểm tra số lần đã dùng
        if self.usage_limit_per_user > 0:
            used_count = VoucherUsage.objects.filter(
                voucher=self,
                user=user
            ).count()
            
            if used_count >= self.usage_limit_per_user:
                return False, "Bạn đã hết lượt sử dụng voucher này"
        
        return True, "OK"
    
    def calculate_discount(self, order_value):
        """Tính số tiền được giảm"""
        if self.discount_type == self.DiscountType.PERCENTAGE:
            discount = order_value * self.discount_value // 100
            
            # Áp dụng giảm tối đa
            if self.max_discount > 0:
                discount = min(discount, self.max_discount)
            
            return discount
        
        elif self.discount_type == self.DiscountType.FIXED:
            return min(self.discount_value, order_value)
        
        elif self.discount_type == self.DiscountType.FREE_SHIP:
            # TODO: Tính phí ship rồi trả về
            return 0
        
        return 0
    
    @property
    def remaining_quantity(self):
        """Số lượng còn lại"""
        if self.total_quantity == 0:
            return None  # Không giới hạn
        return self.total_quantity - self.used_quantity


class VoucherUsage(models.Model):
    """Lịch sử sử dụng voucher"""
    
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order = models.ForeignKey('orders.OrderModel', on_delete=models.CASCADE)
    
    discount_amount = models.PositiveIntegerField(verbose_name='Số tiền được giảm')
    used_at = models.DateTimeField(auto_now_add=True, verbose_name='Thời gian sử dụng')
    
    class Meta:
        ordering = ['-used_at']
        verbose_name = 'Lịch sử sử dụng voucher'
        verbose_name_plural = 'Lịch sử sử dụng voucher'
    
    def __str__(self):
        return "{} - {} - {:,}đ".format(
            self.user.username, 
            self.voucher.code, 
            self.discount_amount
        )


class FlashSale(models.Model):
    """Flash Sale - Giảm giá trong thời gian giới hạn"""
    
    name = models.CharField(max_length=200, verbose_name='Tên chương trình')
    description = models.TextField(blank=True, verbose_name='Mô tả')
    
    discount_percentage = models.PositiveIntegerField(
        verbose_name='% giảm giá',
        help_text='Nhập 20 = giảm 20%'
    )
    
    start_time = models.DateTimeField(verbose_name='Thời gian bắt đầu')
    end_time = models.DateTimeField(verbose_name='Thời gian kết thúc')
    
    # Sản phẩm áp dụng
    products = models.ManyToManyField(
        'catalog.ProductModel',
        through='FlashSaleProduct',
        verbose_name='Sản phẩm'
    )
    
    is_active = models.BooleanField(default=True, verbose_name='Đang hoạt động')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_time']
        verbose_name = 'Flash Sale'
        verbose_name_plural = 'Flash Sale'
    
    def __str__(self):
        return self.name
    
    def is_running(self):
        """Kiểm tra flash sale đang diễn ra không"""
        now = timezone.now()
        return (
            self.is_active and 
            self.start_time <= now <= self.end_time
        )
    
    def time_remaining(self):
        """Thời gian còn lại (seconds)"""
        if not self.is_running():
            return 0
        
        now = timezone.now()
        remaining = (self.end_time - now).total_seconds()
        return max(0, int(remaining))


class FlashSaleProduct(models.Model):
    """Sản phẩm trong Flash Sale"""
    
    flash_sale = models.ForeignKey(FlashSale, on_delete=models.CASCADE)
    product = models.ForeignKey('catalog.ProductModel', on_delete=models.CASCADE)
    
    original_price = models.PositiveIntegerField(verbose_name='Giá gốc')
    sale_price = models.PositiveIntegerField(verbose_name='Giá sale')
    quantity_limit = models.PositiveIntegerField(
        default=0,
        verbose_name='Số lượng giới hạn',
        help_text='0 = không giới hạn'
    )
    sold_quantity = models.PositiveIntegerField(default=0, verbose_name='Đã bán')
    
    class Meta:
        unique_together = ['flash_sale', 'product']
        verbose_name = 'Sản phẩm Flash Sale'
        verbose_name_plural = 'Sản phẩm Flash Sale'
    
    def __str__(self):
        return "{} - {}".format(self.flash_sale.name, self.product.name)
    
    def is_available(self):
        """Còn hàng trong flash sale không"""
        if self.quantity_limit == 0:
            return True
        return self.sold_quantity < self.quantity_limit
    
    @property
    def discount_percentage(self):
        """Tính % giảm giá"""
        if self.original_price == 0:
            return 0
        return int((self.original_price - self.sale_price) * 100 / self.original_price)