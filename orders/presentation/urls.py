from django.urls import path
from .views import CheckoutApi, MyOrdersApi, OrderDetailApi

urlpatterns = [
    path('checkout/', CheckoutApi.as_view(), name='checkout'),
    path('my/', MyOrdersApi.as_view(), name='my_orders'),
    path('<int:order_id>/', OrderDetailApi.as_view(), name='order_detail'),
]