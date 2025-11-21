from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static

from core.views import (
    home_view, shop_view, cart_view, 
    login_page, register_page, profile_view,
    my_orders_view, order_detail_view, contact_view,
    product_detail_view, addresses_view,checkout_view
)

def health(request): 
    return HttpResponse("OK")


urlpatterns = [
    # Frontend Pages
    path('', home_view, name='home'),
    path('shop/', shop_view, name='shop'),
    path('shop/detail/', product_detail_view, name='product_detail'),  # Thêm dòng này
    path('products/<int:product_id>/', product_detail_view, name='product_detail_by_id'),
    path('cart/', cart_view, name='cart'),
    path('checkout/', checkout_view, name='checkout'),
    path('login/', login_page, name='login_page'),
    path('register/', register_page, name='register_page'),
    path('profile/', profile_view, name='profile'),
    path('orders/', my_orders_view, name='my_orders'),
    path('orders/<int:order_id>/', order_detail_view, name='order_detail'),
    path('contact/', contact_view, name='contact'),
    path('addresses/', addresses_view, name='addresses'),
    
    # Admin & Health
    path('admin/', admin.site.urls),
    path('health/', health),
    
    # API URLs
    path('api/accounts/', include('accounts.presentation.urls')),
    path('api/catalog/', include('catalog.presentation.urls')),
    path('api/cart/', include('cart.presentation.urls')),
    path('api/orders/', include('orders.presentation.urls')),
    path('api/payments/', include('payments.presentation.urls')),
    path('api/promotions/', include('promotions.presentation.urls')),
    path('api/notifications/', include('notifications.presentation.urls')),
]

# Serve media files trong development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)