from django.contrib import admin
from .infrastructure.models import User, ShippingAddress


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_farmer', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'phone')
    list_filter = ('is_farmer', 'is_customer', 'is_staff', 'is_superuser')
    readonly_fields = ('date_joined', 'last_login')


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'user', 'province', 'district', 'is_default', 'created_at')
    search_fields = ('full_name', 'phone', 'user__username', 'address_line')
    list_filter = ('is_default', 'province', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Thông tin người nhận', {
            'fields': ('user', 'full_name', 'phone')
        }),
        ('Địa chỉ', {
            'fields': ('province', 'district', 'ward', 'address_line')
        }),
        ('Cài đặt', {
            'fields': ('is_default', 'created_at', 'updated_at')
        }),
    )