from django.shortcuts import render

def home_view(request):
    return render(request, 'home.html')

def shop_view(request):
    return render(request, 'catalog/shop.html')

def product_detail_view(request):
    return render(request, 'catalog/shop-detail.html')

def cart_view(request):
    return render(request, 'cart/cart.html')

def login_page(request):
    return render(request, 'accounts/login_register.html', {'is_login': True})

def register_page(request):
    return render(request, 'accounts/login_register.html', {'is_login': False})

def profile_view(request):
    return render(request, 'accounts/profile.html')

def my_orders_view(request):
    return render(request, 'orders/my_orders.html')

def order_detail_view(request, order_id):
    return render(request, 'orders/order_detail.html', {'order_id': order_id})

def addresses_view(request):
    return render(request, 'addresses.html')

def contact_view(request):
    return render(request, 'contact.html')