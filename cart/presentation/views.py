from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import get_user_model
from cart.infrastructure.models import CartModel, CartItemModel
from catalog.infrastructure.models import ProductModel
class AddToCartApi(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        user = get_user_model().objects.first()
        if not user:
            return Response({'detail':'Chưa có user. Tạo superuser trước.'}, status=400)
        prod_id = int(request.data.get('product_id', 0))
        qty = int(request.data.get('qty', 1))
        p = ProductModel.objects.filter(id=prod_id).first()
        if not p: return Response({'detail':'Sản phẩm không tồn tại'}, status=404)
        cart,_ = CartModel.objects.get_or_create(owner=user)
        item,_ = CartItemModel.objects.get_or_create(cart=cart, product=p)
        item.qty = item.qty + qty
        item.save()
        return Response({'detail':'OK','cart_id': cart.id})
class MyCartApi(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        user = get_user_model().objects.first()
        if not user:
            return Response({'detail':'Chưa có user.'}, status=400)
        cart = CartModel.objects.filter(owner=user).first()
        if not cart:
            return Response({'items':[], 'total_vnd': 0})
        items = [{
            'product_id': it.product_id,
            'name': it.product.name,
            'price_vnd': it.product.price_vnd,
            'qty': it.qty,
            'line_total': it.product.price_vnd * it.qty
        } for it in cart.items.select_related('product')]
        total = sum(i['line_total'] for i in items)
        return Response({'items': items, 'total_vnd': total})
