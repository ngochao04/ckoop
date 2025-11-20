# core/views.py hoặc tạo file mới: frontend/views.py
from django.shortcuts import render

def home_view(request):
    """Trang chủ"""
    return render(request, 'home.html')

def shop_view(request):
    """Trang danh sách sản phẩm"""
    return render(request, 'catalog/shop.html')

def product_detail_view(request, product_id):
    """Trang chi tiết sản phẩm"""
    return render(request, 'catalog/product_detail.html', {'product_id': product_id})

def cart_view(request):
    """Trang giỏ hàng"""
    return render(request, 'cart/cart.html')

def login_page(request):
    """Trang đăng nhập"""
    return render(request, 'accounts/login_register.html', {'is_login': True})

def register_page(request):
    """Trang đăng ký"""
    return render(request, 'accounts/login_register.html', {'is_login': False})

def profile_view(request):
    """Trang profile"""
    return render(request, 'accounts/profile.html')

def my_orders_view(request):
    """Trang đơn hàng của tôi"""
    return render(request, 'orders/my_orders.html')

def order_detail_view(request, order_id):
    """Chi tiết đơn hàng"""
    return render(request, 'orders/order_detail.html', {'order_id': order_id})

def contact_view(request):
    """Trang liên hệ"""
    return render(request, 'contact.html')