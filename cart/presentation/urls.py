from django.urls import path
from .views import AddToCartApi, MyCartApi
urlpatterns = [ path('add/', AddToCartApi.as_view(), name='add_to_cart'),
                path('me/', MyCartApi.as_view(), name='my_cart') ]
