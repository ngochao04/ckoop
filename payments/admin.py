from django.contrib import admin
from django.utils.html import format_html
from .models import Payment, BankAccount, PaymentGatewayConfig


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'order_link', 
        'buyer_name',
        'method', 
        'amount_display',
        'status_badge', 
        'transaction_id',
        'payment_date',
        'created_at'
    )
    list_filter = ('method', 'status', 'created_at', 'payment_date')
    search_fields = ('transaction_id', 'order__id', 'order__buyer__username', 'order__buyer__email')
    readonly_fields = ('order', 'amount', 'created_at', 'updated_at', 'gateway_response_display')
    
    fieldsets = (
        ('Thông tin đơn hàng', {
            'fields': ('order', 'amount')
        }),
        ('Thanh toán', {
            'fields': ('method', 'status', 'transaction_id', 'payment_date')
        }),
        ('Gateway Response', {
            'fields': ('gateway_response_display',),
            'classes': ('collapse',)
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def order_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        url = reverse('admin:orders_ordermodel_change', args=[obj.order.id])
        return format_html('<a href="{}"">Order #{}</a>', url, obj.order.id)
    order_link.short_description = 'Đơn hàng'
    
    def buyer_name(self, obj):
        return obj.order.buyer.username
    buyer_name.short_description = 'Khách hàng'
    
    def amount_display(self, obj):
        return format_html('<strong>{:,} ₫</strong>', obj.amount)
    amount_display.short_description = 'Số tiền'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'paid': '#28a745',
            'failed': '#dc3545',
            'refunded': '#6c757d',
            'cancelled': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Trạng thái'
    
    def gateway_response_display(self, obj):
        import json
        if obj.gateway_response:
            return format_html('<pre>{}</pre>', json.dumps(obj.gateway_response, indent=2, ensure_ascii=False))
        return '-'
    gateway_response_display.short_description = 'Gateway Response'
    
    def has_add_permission(self, request):
        return False


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = (
        'bank_name', 
        'account_number', 
        'account_holder',
        'qr_preview',
        'is_active',
        'display_order'
    )
    list_editable = ('is_active', 'display_order')
    list_filter = ('is_active', 'bank_name')
    search_fields = ('bank_name', 'account_number', 'account_holder')
    
    fieldsets = (
        ('Thông tin ngân hàng', {
            'fields': ('bank_name', 'bank_code', 'branch')
        }),
        ('Tài khoản', {
            'fields': ('account_number', 'account_holder')
        }),
        ('QR Code', {
            'fields': ('qr_code', 'qr_preview_large')
        }),
        ('Cài đặt', {
            'fields': ('is_active', 'display_order')
        }),
    )
    readonly_fields = ('qr_preview_large',)
    
    def qr_preview(self, obj):
        if obj.qr_code:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: contain;" />',
                obj.qr_code.url
            )
        return '-'
    qr_preview.short_description = 'QR Code'
    
    def qr_preview_large(self, obj):
        if obj.qr_code:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px;" />',
                obj.qr_code.url
            )
        return 'Chưa có QR Code'
    qr_preview_large.short_description = 'Xem trước QR Code'


@admin.register(PaymentGatewayConfig)
class PaymentGatewayConfigAdmin(admin.ModelAdmin):
    list_display = (
        'display_name',
        'name',
        'logo_preview',
        'is_active',
        'fees_display'
    )
    list_editable = ('is_active',)
    list_filter = ('is_active',)
    search_fields = ('name', 'display_name')
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('name', 'display_name', 'logo', 'logo_preview_large')
        }),
        ('Phí giao dịch', {
            'fields': ('fixed_fee', 'percentage_fee')
        }),
        ('Cấu hình', {
            'fields': ('is_active', 'config')
        }),
    )
    readonly_fields = ('logo_preview_large',)
    
    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" width="30" height="30" style="object-fit: contain;" />',
                obj.logo.url
            )
        return '-'
    logo_preview.short_description = 'Logo'
    
    def logo_preview_large(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 100px; object-fit: contain;" />',
                obj.logo.url
            )
        return 'Chưa có logo'
    logo_preview_large.short_description = 'Xem trước logo'
    
    def fees_display(self, obj):
        fees = []
        if obj.fixed_fee > 0:
            fees.append(f'{obj.fixed_fee:,}₫')
        if obj.percentage_fee > 0:
            fees.append(f'{obj.percentage_fee}%')
        return ' + '.join(fees) if fees else 'Miễn phí'
    fees_display.short_description = 'Phí'