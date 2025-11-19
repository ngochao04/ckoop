from django.urls import path
from .views import RegisterApi, LoginApi, LogoutApi, ProfileApi

urlpatterns = [
    path('register/', RegisterApi.as_view(), name='register'),
    path('login/', LoginApi.as_view(), name='login'),
    path('logout/', LogoutApi.as_view(), name='logout'),
    path('profile/', ProfileApi.as_view(), name='profile'),
]