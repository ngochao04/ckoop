from django.urls import path
from .views import CheckoutApi
urlpatterns = [ path('checkout/', CheckoutApi.as_view(), name='checkout') ]
