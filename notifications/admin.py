from django.contrib import admin
from django.utils.html import format_html
from .models import Notification, EmailLog, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'type_badge',
        'title',
        'is_read_badge',
        'created_at'
    )
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    readonly_fields = ('user', 'type', 'title', 'message', 'link', 'data', 'created_at', 'read_at')
    
    fieldsets = (
        ('Thông tin', {
            'fields': ('user', 'type', 'title', 'message', 'link')
        }),
        ('Dữ liệu', {
            'fields': ('data',),
            'classes': ('collapse',)
        }),
        ('Trạng thái', {
            'fields': ('is_read', 'read_at', 'created_at')
        }),
    )
    
    def type_badge(self, obj):
        colors = {
            'order_confirmed': '#28a745',
            'order_shipped': '#17a2b8',
            'order_delivered': '#28a745',
            'order_cancelled': '#dc3545',
            'payment_success': '#28a745',
            'payment_failed': '#dc3545',
            'low_stock': '#ffc107',
            'promotion': '#6f42c1',
            'flash_sale': '#fd7e14',
            'system': '#6c757d',
        }
        color = colors.get(obj.type, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_type_display()
        )
    type_badge.short_description = 'Loại'
    
    def is_read_badge(self, obj):
        if obj.is_read:
            return format_html(
                '<span style="color: #28a745;">✓ Đã đọc</span>'
            )
        return format_html(
            '<span style="color: #ffc107; font-weight: bold;">● Chưa đọc</span>'
        )
    is_read_badge.short_description = 'Trạng thái'
    
    def has_add_permission(self, request):
        return False


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'to_email',
        'subject',
        'status_badge',
        'created_at',
        'sent_at'
    )
    list_filter = ('status', 'created_at')
    search_fields = ('to_email', 'subject', 'body')
    readonly_fields = ('to_email', 'subject', 'body', 'user', 'template_name', 'context_data', 'created_at', 'sent_at')
    
    fieldsets = (
        ('Email', {
            'fields': ('to_email', 'subject', 'body')
        }),
        ('Người nhận', {
            'fields': ('user',)
        }),
        ('Trạng thái', {
            'fields': ('status', 'error_message', 'created_at', 'sent_at')
        }),
        ('Template', {
            'fields': ('template_name', 'context_data'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'sent': '#28a745',
            'failed': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Trạng thái'
    
    def has_add_permission(self, request):
        return False


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'email_settings_display',
        'app_settings_display',
        'updated_at'
    )
    search_fields = ('user__username', 'user__email')
    
    fieldsets = (
        ('Người dùng', {
            'fields': ('user',)
        }),
        ('Email Notifications', {
            'fields': ('email_order_updates', 'email_promotions', 'email_flash_sales')
        }),
        ('In-App Notifications', {
            'fields': ('app_order_updates', 'app_promotions', 'app_flash_sales')
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def email_settings_display(self, obj):
        enabled = []
        if obj.email_order_updates:
            enabled.append('Đơn hàng')
        if obj.email_promotions:
            enabled.append('KM')
        if obj.email_flash_sales:
            enabled.append('Flash Sale')
        
        if enabled:
            return format_html(
                '<span style="color: #28a745;">✓ {}</span>',
                ', '.join(enabled)
            )
        return format_html('<span style="color: #999;">✗ Tắt hết</span>')
    email_settings_display.short_description = 'Email'
    
    def app_settings_display(self, obj):
        enabled = []
        if obj.app_order_updates:
            enabled.append('Đơn hàng')
        if obj.app_promotions:
            enabled.append('KM')
        if obj.app_flash_sales:
            enabled.append('Flash Sale')
        
        if enabled:
            return format_html(
                '<span style="color: #28a745;">✓ {}</span>',
                ', '.join(enabled)
            )
        return format_html('<span style="color: #999;">✗ Tắt hết</span>')
    app_settings_display.short_description = 'App'