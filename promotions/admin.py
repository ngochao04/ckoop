from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Voucher, VoucherUsage, FlashSale, FlashSaleProduct


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'name',
        'discount_display',
        'usage_display',
        'validity_badge',
        'is_active',
        'is_public',
        'start_date',
        'end_date'
    )
    list_filter = ('is_active', 'is_public', 'discount_type', 'start_date', 'end_date')
    search_fields = ('code', 'name', 'description')
    list_editable = ('is_active', 'is_public')
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('code', 'name', 'description')
        }),
        ('Giảm giá', {
            'fields': ('discount_type', 'discount_value', 'max_discount')
        }),
        ('Điều kiện', {
            'fields': ('min_order_value',)
        }),
        ('Số lượng', {
            'fields': ('total_quantity', 'used_quantity', 'usage_limit_per_user')
        }),
        ('Thời gian', {
            'fields': ('start_date', 'end_date')
        }),
        ('Cài đặt', {
            'fields': ('is_active', 'is_public')
        }),
        ('Áp dụng cho', {
            'fields': ('applicable_products', 'applicable_categories'),
            'classes': ('collapse',)
        }),
    )
    
    filter_horizontal = ('applicable_products', 'applicable_categories')
    readonly_fields = ('used_quantity',)
    
    def discount_display(self, obj):
        if obj.discount_type == 'percentage':
            text = f"{obj.discount_value}%"
            if obj.max_discount > 0:
                text += f" (max {obj.max_discount:,}₫)"
        elif obj.discount_type == 'fixed':
            text = f"{obj.discount_value:,}₫"
        else:
            text = "Free Ship"
        return text
    discount_display.short_description = 'Giảm giá'
    
    def usage_display(self, obj):
        if obj.total_quantity > 0:
            percent = (obj.used_quantity / obj.total_quantity) * 100
            color = '#28a745' if percent < 50 else '#ffc107' if percent < 80 else '#dc3545'
            return format_html(
                '<span style="color: {};">{}/{} ({}%)</span>',
                color,
                obj.used_quantity,
                obj.total_quantity,
                int(percent)
            )
        return f"{obj.used_quantity}/∞"
    usage_display.short_description = 'Sử dụng'
    
    def validity_badge(self, obj):
        is_valid, message = obj.is_valid()
        if is_valid:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">✓ Hợp lệ</span>'
            )
        else:
            return format_html(
                '<span style="background: #dc3545; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">✗ {}</span>',
                message
            )
    validity_badge.short_description = 'Trạng thái'


@admin.register(VoucherUsage)
class VoucherUsageAdmin(admin.ModelAdmin):
    list_display = ('voucher_code', 'user', 'order_link', 'discount_amount', 'used_at')
    list_filter = ('used_at', 'voucher')
    search_fields = ('voucher__code', 'user__username', 'user__email', 'order__id')
    readonly_fields = ('voucher', 'user', 'order', 'discount_amount', 'used_at')
    
    def voucher_code(self, obj):
        return obj.voucher.code
    voucher_code.short_description = 'Mã voucher'
    
    def order_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:orders_ordermodel_change', args=[obj.order.id])
        return format_html('<a href="{}">Order #{}</a>', url, obj.order.id)
    order_link.short_description = 'Đơn hàng'
    
    def has_add_permission(self, request):
        return False


class FlashSaleProductInline(admin.TabularInline):
    model = FlashSaleProduct
    extra = 1
    fields = ('product', 'original_price', 'sale_price', 'quantity_limit', 'sold_quantity')
    readonly_fields = ('sold_quantity',)


@admin.register(FlashSale)
class FlashSaleAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'discount_percentage_display',
        'time_display',
        'status_badge',
        'product_count',
        'is_active'
    )
    list_filter = ('is_active', 'start_time', 'end_time')
    search_fields = ('name', 'description')
    list_editable = ('is_active',)
    inlines = [FlashSaleProductInline]
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('name', 'description', 'discount_percentage')
        }),
        ('Thời gian', {
            'fields': ('start_time', 'end_time')
        }),
        ('Cài đặt', {
            'fields': ('is_active',)
        }),
    )
    
    def discount_percentage_display(self, obj):
        return format_html(
            '<strong style="color: #dc3545; font-size: 16px;">-{}%</strong>',
            obj.discount_percentage
        )
    discount_percentage_display.short_description = 'Giảm giá'
    
    def time_display(self, obj):
        # FIX: Format dates as strings first, then pass to format_html
        start_str = obj.start_time.strftime('%d/%m/%Y %H:%M')
        end_str = obj.end_time.strftime('%d/%m/%Y %H:%M')
        
        return format_html(
            '<div style="font-size: 11px;"><strong>Bắt đầu:</strong> {}<br><strong>Kết thúc:</strong> {}</div>',
            start_str,
            end_str
        )
    time_display.short_description = 'Thời gian'
    
    def status_badge(self, obj):
        now = timezone.now()
        
        if obj.is_running():
            remaining = obj.time_remaining()
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            # FIX: Format time string first, then pass to format_html
            time_str = f"{hours:02d}:{minutes:02d}"
            return format_html(
                '<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">🔥 Đang diễn ra ({})</span>',
                time_str
            )
        elif now < obj.start_time:
            return format_html(
                '<span style="background: #ffc107; color: black; padding: 3px 8px; border-radius: 3px; font-size: 11px;">⏰ Sắp diễn ra</span>'
            )
        else:
            return format_html(
                '<span style="background: #6c757d; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">✓ Đã kết thúc</span>'
            )
    status_badge.short_description = 'Trạng thái'
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Số sản phẩm'


@admin.register(FlashSaleProduct)
class FlashSaleProductAdmin(admin.ModelAdmin):
    list_display = (
        'flash_sale',
        'product',
        'price_display',
        'discount_display',
        'quantity_display',
        'availability_badge'
    )
    list_filter = ('flash_sale',)
    search_fields = ('product__name', 'flash_sale__name')
    readonly_fields = ('sold_quantity',)
    
    def price_display(self, obj):
        # FIX: Format prices as strings first to avoid format string conflicts
        original_price_str = f"{obj.original_price:,}₫"
        sale_price_str = f"{obj.sale_price:,}₫"
        
        return format_html(
            '<div><del style="color: #999;">{}</del><br><strong style="color: #dc3545; font-size: 14px;">{}</strong></div>',
            original_price_str,
            sale_price_str
        )
    price_display.short_description = 'Giá'
    
    def discount_display(self, obj):
        return format_html(
            '<span style="background: #dc3545; color: white; padding: 2px 6px; border-radius: 3px;">-{}%</span>',
            obj.discount_percentage
        )
    discount_display.short_description = 'Giảm'
    
    def quantity_display(self, obj):
        if obj.quantity_limit > 0:
            percent = (obj.sold_quantity / obj.quantity_limit) * 100
            return f"{obj.sold_quantity}/{obj.quantity_limit} ({percent:.0f}%)"
        return f"{obj.sold_quantity}/∞"
    quantity_display.short_description = 'Đã bán'
    
    def availability_badge(self, obj):
        if obj.is_available():
            return format_html(
                '<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">✓ Còn hàng</span>'
            )
        return format_html(
            '<span style="background: #dc3545; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">✗ Hết hàng</span>'
        )
    availability_badge.short_description = 'Tình trạng'