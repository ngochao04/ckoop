from django.db import models
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)
    
    class Meta: 
        verbose_name_plural = 'Categories'
    
    def __str__(self): 
        return self.name


class ProductModel(models.Model):
    name = models.CharField(max_length=180)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price_vnd = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=64, unique=True)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)
    thumbnail = models.ImageField(upload_to='products/', blank=True)
    
    # Inventory fields (Phase 1)
    stock_quantity = models.PositiveIntegerField(default=0, verbose_name='Số lượng tồn kho')
    low_stock_threshold = models.PositiveIntegerField(default=10, verbose_name='Ngưỡng cảnh báo hết hàng')
    weight_grams = models.PositiveIntegerField(default=0, verbose_name='Khối lượng (gram)')
    unit = models.CharField(max_length=20, default='kg', verbose_name='Đơn vị')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['is_active', '-created_at']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['stock_quantity']),
        ]
    
    def __str__(self): 
        return self.name
    
    @property
    def is_low_stock(self):
        """Kiểm tra sắp hết hàng"""
        return self.stock_quantity <= self.low_stock_threshold
    
    @property
    def is_out_of_stock(self):
        """Kiểm tra hết hàng"""
        return self.stock_quantity == 0
    
    def reduce_stock(self, quantity):
        """Giảm tồn kho"""
        if self.stock_quantity < quantity:
            raise ValueError(f'Không đủ hàng trong kho. Còn {self.stock_quantity}, yêu cầu {quantity}')
        self.stock_quantity -= quantity
        self.save()
    
    def increase_stock(self, quantity):
        """Tăng tồn kho"""
        self.stock_quantity += quantity
        self.save()


class InventoryLog(models.Model):
    """Nhật ký xuất nhập tồn kho"""
    class Action(models.TextChoices):
        IN = 'in', 'Nhập kho'
        OUT = 'out', 'Xuất kho'
        ADJUST = 'adjust', 'Điều chỉnh'
        RETURN = 'return', 'Trả hàng'
    
    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE, related_name='inventory_logs')
    action = models.CharField(max_length=10, choices=Action.choices)
    quantity = models.IntegerField(verbose_name='Số lượng thay đổi')
    previous_stock = models.PositiveIntegerField(verbose_name='Tồn kho trước')
    new_stock = models.PositiveIntegerField(verbose_name='Tồn kho sau')
    note = models.TextField(blank=True, verbose_name='Ghi chú')
    order = models.ForeignKey('orders.OrderModel', on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Nhật ký tồn kho'
        verbose_name_plural = 'Nhật ký tồn kho'
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.product.name} - {self.quantity}"


class Wishlist(models.Model):
    """Danh sách yêu thích"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'product']
        verbose_name = 'Sản phẩm yêu thích'
        verbose_name_plural = 'Sản phẩm yêu thích'
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class ProductReview(models.Model):
    """Đánh giá sản phẩm"""
    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order = models.ForeignKey('orders.OrderModel', on_delete=models.SET_NULL, null=True, blank=True)
    rating = models.PositiveSmallIntegerField()  # 1-5 sao
    title = models.CharField(max_length=200, verbose_name='Tiêu đề')
    content = models.TextField(verbose_name='Nội dung đánh giá')
    images = models.JSONField(default=list, blank=True)  # List URLs ảnh
    is_verified_purchase = models.BooleanField(default=False, verbose_name='Đã mua hàng')
    helpful_count = models.PositiveIntegerField(default=0, verbose_name='Số người thấy hữu ích')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['product', 'user', 'order']
        ordering = ['-created_at']
        verbose_name = 'Đánh giá sản phẩm'
        verbose_name_plural = 'Đánh giá sản phẩm'
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name} - {self.rating}⭐"


class ReviewHelpful(models.Model):
    """Người dùng đánh giá review hữu ích"""
    review = models.ForeignKey(ProductReview, on_delete=models.CASCADE, related_name='helpful_votes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['review', 'user']
        verbose_name = 'Vote hữu ích'
        verbose_name_plural = 'Vote hữu ích'