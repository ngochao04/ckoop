from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True)
    is_farmer = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=True)


class ShippingAddress(models.Model):
    """Địa chỉ giao hàng của khách hàng"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    full_name = models.CharField(max_length=150, verbose_name='Họ tên')
    phone = models.CharField(max_length=20, verbose_name='Số điện thoại')
    province = models.CharField(max_length=100, verbose_name='Tỉnh/Thành phố')
    district = models.CharField(max_length=100, verbose_name='Quận/Huyện')
    ward = models.CharField(max_length=100, verbose_name='Phường/Xã')
    address_line = models.CharField(max_length=255, verbose_name='Địa chỉ cụ thể')
    is_default = models.BooleanField(default=False, verbose_name='Địa chỉ mặc định')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Địa chỉ giao hàng'
        verbose_name_plural = 'Địa chỉ giao hàng'
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.full_name} - {self.address_line}, {self.ward}, {self.district}, {self.province}"
    
    def save(self, *args, **kwargs):
        # Nếu đặt làm mặc định, bỏ mặc định của các địa chỉ khác
        if self.is_default:
            ShippingAddress.objects.filter(
                user=self.user, 
                is_default=True
            ).exclude(id=self.id).update(is_default=False)
        
        # Nếu đây là địa chỉ đầu tiên, tự động đặt làm mặc định
        if not self.id and not ShippingAddress.objects.filter(user=self.user).exists():
            self.is_default = True
        
        super().save(*args, **kwargs)