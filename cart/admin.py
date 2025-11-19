from django.contrib import admin
from .infrastructure.models import CartModel, CartItemModel


class CartItemInline(admin.TabularInline):
    model = CartItemModel
    extra = 0
    readonly_fields = ('product', 'qty')
    can_delete = True


@admin.register(CartModel)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'items_count', 'created_at')
    search_fields = ('owner__username', 'owner__email')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)
    inlines = [CartItemInline]
    
    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'Số items'