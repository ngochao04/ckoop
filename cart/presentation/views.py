from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import TokenAuthentication
from django.shortcuts import get_object_or_404

from cart.infrastructure.models import CartModel, CartItemModel
from catalog.infrastructure.models import ProductModel


class AddToCartApi(APIView):
    """Thêm sản phẩm vào giỏ hàng"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user = request.user
        prod_id = int(request.data.get('product_id', 0))
        qty = int(request.data.get('qty', 1))
        
        if qty <= 0:
            return Response({
                'detail': 'Số lượng phải lớn hơn 0'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        p = ProductModel.objects.filter(id=prod_id, is_active=True).first()
        if not p:
            return Response({
                'detail': 'Sản phẩm không tồn tại hoặc đã ngừng bán'
            }, status=status.HTTP_404_NOT_FOUND)
        
        cart, _ = CartModel.objects.get_or_create(owner=user)
        item, created = CartItemModel.objects.get_or_create(
            cart=cart, 
            product=p,
            defaults={'qty': 0}
        )
        
        item.qty = item.qty + qty
        item.save()
        
        return Response({
            'detail': 'Đã thêm vào giỏ hàng',
            'cart_id': cart.id,
            'product_name': p.name,
            'qty': item.qty
        })


class MyCartApi(APIView):
    """Xem giỏ hàng của tôi"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        cart = CartModel.objects.filter(owner=user).first()
        
        if not cart:
            return Response({
                'items': [],
                'total_vnd': 0,
                'total_items': 0
            })
        
        items = [{
            'id': it.id,
            'product_id': it.product_id,
            'name': it.product.name,
            'price_vnd': it.product.price_vnd,
            'qty': it.qty,
            'line_total': it.product.price_vnd * it.qty
        } for it in cart.items.select_related('product').filter(product__is_active=True)]
        
        total = sum(i['line_total'] for i in items)
        total_items = sum(i['qty'] for i in items)
        
        return Response({
            'items': items,
            'total_vnd': total,
            'total_items': total_items
        })


class CartItemUpdateApi(APIView):
    """Cập nhật số lượng item trong giỏ"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def put(self, request, item_id):
        user = request.user
        new_qty = int(request.data.get('qty', 1))
        
        if new_qty <= 0:
            return Response({
                'detail': 'Số lượng phải lớn hơn 0'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Lấy item và kiểm tra quyền sở hữu
        item = get_object_or_404(
            CartItemModel.objects.select_related('cart'), 
            id=item_id, 
            cart__owner=user
        )
        
        item.qty = new_qty
        item.save()
        
        return Response({
            'detail': 'Đã cập nhật số lượng',
            'item_id': item.id,
            'qty': item.qty,
            'line_total': item.product.price_vnd * item.qty
        })


class CartItemRemoveApi(APIView):
    """Xóa item khỏi giỏ hàng"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, item_id):
        user = request.user
        
        item = get_object_or_404(
            CartItemModel.objects.select_related('cart'),
            id=item_id,
            cart__owner=user
        )
        
        product_name = item.product.name
        item.delete()
        
        return Response({
            'detail': f'Đã xóa {product_name} khỏi giỏ hàng'
        })


class CartClearApi(APIView):
    """Xóa toàn bộ giỏ hàng"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user = request.user
        cart = CartModel.objects.filter(owner=user).first()
        
        if cart:
            items_count = cart.items.count()
            cart.items.all().delete()
            
            return Response({
                'detail': f'Đã xóa {items_count} sản phẩm khỏi giỏ hàng'
            })
        
        return Response({
            'detail': 'Giỏ hàng đã trống'
        })