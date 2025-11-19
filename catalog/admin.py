from django.contrib import admin
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
    list_display = ('name', 'sku', 'price_vnd', 'category', 'is_active', 'created_at')
    search_fields = ('name', 'sku', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_active', 'category', 'created_at')
    list_editable = ('price_vnd', 'is_active')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('name', 'slug', 'sku', 'category')
        }),
        ('Giá & Trạng thái', {
            'fields': ('price_vnd', 'is_active')
        }),
        ('Mô tả & Hình ảnh', {
            'fields': ('description', 'thumbnail')
        }),
        ('Thời gian', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )