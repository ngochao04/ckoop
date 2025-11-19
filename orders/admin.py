from django.contrib import admin
from .infrastructure.models import OrderModel, OrderLineModel


class OrderLineInline(admin.TabularInline):
    model = OrderLineModel
    extra = 0
    readonly_fields = ('product_name', 'sku', 'price_vnd', 'qty')
    can_delete = False


@admin.register(OrderModel)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'total_vnd', 'status', 'created_at')
    search_fields = ('buyer__username', 'buyer__email')
    list_filter = ('status', 'created_at')
    readonly_fields = ('buyer', 'total_vnd', 'created_at')
    inlines = [OrderLineInline]
    
    fieldsets = (
        ('Thông tin đơn hàng', {
            'fields': ('buyer', 'total_vnd', 'status')
        }),
        ('Thời gian', {
            'fields': ('created_at',)
        }),
    )
    
    def has_add_permission(self, request):
        # Không cho phép tạo order từ admin
        return False