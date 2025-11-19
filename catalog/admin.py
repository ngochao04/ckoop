from django.contrib import admin
from django.utils.html import format_html
from .infrastructure.models import (
    Category, ProductModel, InventoryLog, 
    Wishlist, ProductReview, ReviewHelpful
)


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
        'thumbnail_preview',
        'name', 
        'sku', 
        'price_vnd',
        'stock_quantity',  # ← THÊM
        'stock_status',    # ← THÊM
        'category', 
        'is_active', 
        'created_at'
    )
    search_fields = ('name', 'sku', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_active', 'category', 'created_at')
    list_editable = ('price_vnd', 'is_active', 'stock_quantity')  # ← SỬA
    readonly_fields = ('thumbnail_preview_large', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('name', 'slug', 'sku', 'category')
        }),
        ('Giá & Trạng thái', {
            'fields': ('price_vnd', 'is_active')
        }),
        ('Tồn kho', {  # ← THÊM
            'fields': ('stock_quantity', 'low_stock_threshold', 'weight_grams', 'unit')
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
        if obj.thumbnail:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 300px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />',
                obj.thumbnail.url
            )
        return format_html(
            '<div style="width:200px; height:200px; background:#f0f0f0; border-radius:8px; display:flex; align-items:center; justify-content:center; color:#999; border: 2px dashed #ccc;">Chưa có ảnh</div>'
        )
    thumbnail_preview_large.short_description = 'Xem trước ảnh'
    
    def stock_status(self, obj):  # ← THÊM
        if obj.is_out_of_stock:
            return format_html('<span style="color: red; font-weight: bold;">❌ Hết hàng</span>')
        elif obj.is_low_stock:
            return format_html('<span style="color: orange; font-weight: bold;">⚠️ Sắp hết</span>')
        return format_html('<span style="color: green;">✅ Còn hàng</span>')
    stock_status.short_description = 'Trạng thái kho'


# ← THÊM MỚI
@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ('product', 'action', 'quantity', 'previous_stock', 'new_stock', 'created_by', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('product__name', 'product__sku', 'note')
    readonly_fields = ('product', 'action', 'quantity', 'previous_stock', 'new_stock', 'order', 'created_by', 'created_at', 'note')
    
    def has_add_permission(self, request):
        return False  # Không cho phép tạo log thủ công
    
    def has_delete_permission(self, request, obj=None):
        return False  # Không cho phép xóa log


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    search_fields = ('user__username', 'product__name')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'title', 'is_verified_purchase', 'helpful_count', 'created_at')
    search_fields = ('product__name', 'user__username', 'title', 'content')
    list_filter = ('rating', 'is_verified_purchase', 'created_at')
    readonly_fields = ('product', 'user', 'order', 'helpful_count', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Thông tin review', {
            'fields': ('product', 'user', 'order', 'rating', 'is_verified_purchase')
        }),
        ('Nội dung', {
            'fields': ('title', 'content', 'images')
        }),
        ('Thống kê', {
            'fields': ('helpful_count', 'created_at', 'updated_at')
        }),
    )


@admin.register(ReviewHelpful)
class ReviewHelpfulAdmin(admin.ModelAdmin):
    list_display = ('review', 'user', 'created_at')
    search_fields = ('review__product__name', 'user__username')
    list_filter = ('created_at',)
    readonly_fields = ('review', 'user', 'created_at')