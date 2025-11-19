from django.urls import path
from .views import (
    AddToCartApi, MyCartApi, 
    CartItemUpdateApi, CartItemRemoveApi, 
    CartClearApi
)

urlpatterns = [
    path('add/', AddToCartApi.as_view(), name='add_to_cart'),
    path('me/', MyCartApi.as_view(), name='my_cart'),
    path('item/<int:item_id>/', CartItemUpdateApi.as_view(), name='cart_item_update'),
    path('item/<int:item_id>/remove/', CartItemRemoveApi.as_view(), name='cart_item_remove'),
    path('clear/', CartClearApi.as_view(), name='cart_clear'),
]