from django.urls import path
from .views import (
    PaymentMethodsApi, CreatePaymentApi, PaymentDetailApi,
    ConfirmPaymentApi, AdminVerifyPaymentApi, 
    AdminPendingPaymentsApi, MyPaymentsApi
)
from .gateway_views import (
    VNPayCreatePaymentApi, VNPayReturnView,
    MoMoCreatePaymentApi, MoMoReturnView, MoMoNotifyView,
    TestPaymentSuccessView
)

urlpatterns = [
    # Public
    path('methods/', PaymentMethodsApi.as_view(), name='payment_methods'),
    
    # Customer
    path('create/<int:order_id>/', CreatePaymentApi.as_view(), name='create_payment'),
    path('<int:payment_id>/', PaymentDetailApi.as_view(), name='payment_detail'),
    path('<int:payment_id>/confirm/', ConfirmPaymentApi.as_view(), name='confirm_payment'),
    path('my/', MyPaymentsApi.as_view(), name='my_payments'),
    
    # VNPay
    path('vnpay/create/', VNPayCreatePaymentApi.as_view(), name='vnpay_create'),
    path('vnpay/return/', VNPayReturnView.as_view(), name='vnpay_return'),
    
    # MoMo
    path('momo/create/', MoMoCreatePaymentApi.as_view(), name='momo_create'),
    path('momo/return/', MoMoReturnView.as_view(), name='momo_return'),
    path('momo/notify/', MoMoNotifyView.as_view(), name='momo_notify'),
    
    # Test
    path('success/', TestPaymentSuccessView.as_view(), name='payment_success'),
    
    # Admin
    path('admin/pending/', AdminPendingPaymentsApi.as_view(), name='admin_pending_payments'),
    path('admin/<int:payment_id>/verify/', AdminVerifyPaymentApi.as_view(), name='admin_verify_payment'),
]