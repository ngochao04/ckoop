from django.urls import path
from .views import (
    CheckoutApi, MyOrdersApi, OrderDetailApi, CancelOrderApi,
    # Admin APIs
    AdminAllOrdersApi, AdminUpdateOrderStatusApi, 
    AdminDashboardApi, AdminCustomersApi
)

urlpatterns = [
    # Customer APIs
    path('checkout/', CheckoutApi.as_view(), name='checkout'),
    path('my/', MyOrdersApi.as_view(), name='my_orders'),
    path('<int:order_id>/', OrderDetailApi.as_view(), name='order_detail'),
    path('<int:order_id>/cancel/', CancelOrderApi.as_view(), name='cancel_order'),
    
    # Admin APIs
    path('admin/all/', AdminAllOrdersApi.as_view(), name='admin_all_orders'),
    path('admin/<int:order_id>/status/', AdminUpdateOrderStatusApi.as_view(), name='admin_update_status'),
    path('admin/dashboard/', AdminDashboardApi.as_view(), name='admin_dashboard'),
    path('admin/customers/', AdminCustomersApi.as_view(), name='admin_customers'),
]