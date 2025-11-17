from django.urls import path
from .views import ProductListCreateApi
urlpatterns = [ path('products/', ProductListCreateApi.as_view(), name='product_list_create'), ]
