from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
def health(request): return HttpResponse("OK")
urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health),
    path('api/accounts/', include('accounts.presentation.urls')),
    path('api/catalog/', include('catalog.presentation.urls')),
    path('api/cart/', include('cart.presentation.urls')),
    path('api/orders/', include('orders.presentation.urls')),
]
