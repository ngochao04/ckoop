from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.conf.urls.static import static

def health(request): 
    return HttpResponse("OK")

def home(request):
    """Trang chủ - Danh sách API endpoints"""
    return JsonResponse({
        'message': 'CleanAgri API',
        'version': '1.0',
        'endpoints': {
            'health': '/health/',
            'admin': '/admin/',
            'accounts': {
                'register': '/api/accounts/register/',
                'login': '/api/accounts/login/',
                'logout': '/api/accounts/logout/',
                'profile': '/api/accounts/profile/',
            },
            'catalog': {
                'products': '/api/catalog/products/',
                'product_detail': '/api/catalog/products/{id}/',
                'categories': '/api/catalog/categories/',
                'featured': '/api/catalog/featured/',
                'search': '/api/catalog/search/suggestions/',
            },
            'cart': {
                'add': '/api/cart/add/',
                'view': '/api/cart/me/',
                'update_item': '/api/cart/item/{id}/',
                'remove_item': '/api/cart/item/{id}/remove/',
                'clear': '/api/cart/clear/',
            },
            'orders': {
                'checkout': '/api/orders/checkout/',
                'my_orders': '/api/orders/my/',
                'order_detail': '/api/orders/{id}/',
                'cancel': '/api/orders/{id}/cancel/',
                'admin_orders': '/api/orders/admin/all/',
                'update_status': '/api/orders/admin/{id}/status/',
                'admin_dashboard': '/api/orders/admin/dashboard/',
                'admin_customers': '/api/orders/admin/customers/',
            }
        }
    }, json_dumps_params={'indent': 2})

urlpatterns = [
    path('', home),
    path('admin/', admin.site.urls),
    path('health/', health),
    path('api/accounts/', include('accounts.presentation.urls')),
    path('api/catalog/', include('catalog.presentation.urls')),
    path('api/cart/', include('cart.presentation.urls')),
    path('api/orders/', include('orders.presentation.urls')),
]

# Serve media files trong development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)