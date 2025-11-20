from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.conf.urls.static import static

from core.views import home_view

def health(request): 
    return HttpResponse("OK")


urlpatterns = [
    path('', home_view, name='home'),
    path('admin/', admin.site.urls),
    path('health/', health),
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
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)