from django.urls import path
from .views import (
    ProductListCreateApi, ProductDetailApi,
    CategoryListCreateApi, CategoryDetailApi,
    FeaturedProductsApi, SearchSuggestionsApi
)
from .inventory_views import (
    InventoryStockApi, InventoryAdjustApi, 
    InventoryLogApi, LowStockAlertApi
)
from .wishlist_views import (
    WishlistApi, WishlistRemoveApi, WishlistCheckApi
)
from .review_views import (
    ProductReviewListApi, ProductReviewCreateApi,
    ReviewHelpfulApi, MyReviewsApi
)

urlpatterns = [
    # Products
    path('products/', ProductListCreateApi.as_view(), name='product_list_create'),
    path('products/<int:product_id>/', ProductDetailApi.as_view(), name='product_detail'),
    
    # Categories
    path('categories/', CategoryListCreateApi.as_view(), name='category_list_create'),
    path('categories/<int:category_id>/', CategoryDetailApi.as_view(), name='category_detail'),
    
    # Featured & Search
    path('featured/', FeaturedProductsApi.as_view(), name='featured_products'),
    path('search/suggestions/', SearchSuggestionsApi.as_view(), name='search_suggestions'),
    
    # Inventory Management (Admin)
    path('inventory/stock/', InventoryStockApi.as_view(), name='inventory_stock'),
    path('inventory/adjust/<int:product_id>/', InventoryAdjustApi.as_view(), name='inventory_adjust'),
    path('inventory/logs/', InventoryLogApi.as_view(), name='inventory_logs'),
    path('inventory/alerts/', LowStockAlertApi.as_view(), name='low_stock_alerts'),
    
    # Wishlist
    path('wishlist/', WishlistApi.as_view(), name='wishlist'),
    path('wishlist/remove/<int:product_id>/', WishlistRemoveApi.as_view(), name='wishlist_remove'),
    path('wishlist/check/<int:product_id>/', WishlistCheckApi.as_view(), name='wishlist_check'),
    
    # Reviews
    path('products/<int:product_id>/reviews/', ProductReviewListApi.as_view(), name='product_reviews'),
    path('products/<int:product_id>/reviews/create/', ProductReviewCreateApi.as_view(), name='create_review'),
    path('reviews/<int:review_id>/helpful/', ReviewHelpfulApi.as_view(), name='review_helpful'),
    path('reviews/my/', MyReviewsApi.as_view(), name='my_reviews'),
]