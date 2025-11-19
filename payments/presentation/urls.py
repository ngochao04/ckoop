from django.urls import path
from .views import (
    PaymentMethodsApi, CreatePaymentApi, PaymentDetailApi,
    ConfirmPaymentApi, AdminVerifyPaymentApi, 
    AdminPendingPaymentsApi, MyPaymentsApi
)

urlpatterns = [
    # Public
    path('methods/', PaymentMethodsApi.as_view(), name='payment_methods'),
    
    # Customer
    path('create/<int:order_id>/', CreatePaymentApi.as_view(), name='create_payment'),
    path('<int:payment_id>/', PaymentDetailApi.as_view(), name='payment_detail'),
    path('<int:payment_id>/confirm/', ConfirmPaymentApi.as_view(), name='confirm_payment'),
    path('my/', MyPaymentsApi.as_view(), name='my_payments'),
    
    # Admin
    path('admin/pending/', AdminPendingPaymentsApi.as_view(), name='admin_pending_payments'),
    path('admin/<int:payment_id>/verify/', AdminVerifyPaymentApi.as_view(), name='admin_verify_payment'),
]