from django.urls import path
from .views import (
    PublicVouchersApi, CheckVoucherApi, MyVoucherUsageApi,
    ActiveFlashSalesApi, FlashSaleDetailApi, UpcomingFlashSalesApi,
    AdminVoucherListApi, AdminVoucherStatsApi
)

urlpatterns = [
    # Public Vouchers
    path('vouchers/', PublicVouchersApi.as_view(), name='public_vouchers'),
    path('vouchers/check/', CheckVoucherApi.as_view(), name='check_voucher'),
    path('vouchers/my-usage/', MyVoucherUsageApi.as_view(), name='my_voucher_usage'),
    
    # Flash Sales
    path('flash-sales/active/', ActiveFlashSalesApi.as_view(), name='active_flash_sales'),
    path('flash-sales/upcoming/', UpcomingFlashSalesApi.as_view(), name='upcoming_flash_sales'),
    path('flash-sales/<int:flash_sale_id>/', FlashSaleDetailApi.as_view(), name='flash_sale_detail'),
    
    # Admin
    path('admin/vouchers/', AdminVoucherListApi.as_view(), name='admin_vouchers'),
    path('admin/vouchers/<int:voucher_id>/stats/', AdminVoucherStatsApi.as_view(), name='admin_voucher_stats'),
]