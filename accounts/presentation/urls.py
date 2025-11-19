from django.urls import path
from .views import RegisterApi, LoginApi, LogoutApi, ProfileApi
from .address_views import (
    AddressListCreateApi, AddressDetailApi, 
    SetDefaultAddressApi, AddressProvinceApi
)

urlpatterns = [
    # User authentication
    path('register/', RegisterApi.as_view(), name='register'),
    path('login/', LoginApi.as_view(), name='login'),
    path('logout/', LogoutApi.as_view(), name='logout'),
    path('profile/', ProfileApi.as_view(), name='profile'),
    
    # Shipping addresses
    path('addresses/', AddressListCreateApi.as_view(), name='address_list_create'),
    path('addresses/<int:address_id>/', AddressDetailApi.as_view(), name='address_detail'),
    path('addresses/<int:address_id>/set-default/', SetDefaultAddressApi.as_view(), name='address_set_default'),
    
    # Helper data
    path('provinces/', AddressProvinceApi.as_view(), name='provinces_list'),
]