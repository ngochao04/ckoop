from django.contrib import admin
from django.utils.html import format_html
from .infrastructure.models import Category, ProductModel


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'products_count')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('parent',)
    
    def products_count(self, obj):
        return obj.productmodel_set.filter(is_active=True).count()
    products_count.short_description = 'Số sản phẩm'


@admin.register(ProductModel)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'thumbnail_preview',  # Thêm thumbnail preview
        'name', 
        'sku', 
        'price_vnd', 
        'category', 
        'is_active', 
        'created_at'
    )
    search_fields = ('name', 'sku', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_active', 'category', 'created_at')
    list_editable = ('price_vnd', 'is_active')
    readonly_fields = ('thumbnail_preview_large', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('name', 'slug', 'sku', 'category')
        }),
        ('Giá & Trạng thái', {
            'fields': ('price_vnd', 'is_active')
        }),
        ('Mô tả & Hình ảnh', {
            'fields': ('description', 'thumbnail', 'thumbnail_preview_large')
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def thumbnail_preview(self, obj):
        """Hiển thị thumbnail nhỏ trong list view"""
        if obj.thumbnail:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />',
                obj.thumbnail.url
            )
        return format_html(
            '<div style="width:50px; height:50px; background:#ddd; border-radius:4px; display:flex; align-items:center; justify-content:center; font-size:10px; color:#999;">No Image</div>'
        )
    thumbnail_preview.short_description = 'Ảnh'
    
    def thumbnail_preview_large(self, obj):
        """Hiển thị thumbnail lớn trong detail view"""
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />',
                obj.thumbnail.url
            )
        return format_html(
            '<div style="width:200px; height:200px; background:#f0f0f0; border-radius:8px; display:flex; align-items:center; justify-content:center; color:#999; border: 2px dashed #ccc;">Chưa có ảnh</div>'
        )
    thumbnail_preview_large.short_description = 'Xem trước ảnh'