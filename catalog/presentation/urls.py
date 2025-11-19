from django.urls import path
from .views import (
    ProductListCreateApi, ProductDetailApi,
    CategoryListCreateApi, CategoryDetailApi,
    FeaturedProductsApi, SearchSuggestionsApi
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
]