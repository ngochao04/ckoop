from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import TokenAuthentication
from django.shortcuts import get_object_or_404

from catalog.infrastructure.models import Wishlist, ProductModel


class WishlistApi(APIView):
    """Quản lý danh sách yêu thích"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Xem danh sách yêu thích"""
        wishlist_items = Wishlist.objects.filter(
            user=request.user
        ).select_related('product')
        
        data = [{
            'id': item.id,
            'product': {
                'id': item.product.id,
                'name': item.product.name,
                'slug': item.product.slug,
                'price_vnd': item.product.price_vnd,
                'thumbnail': item.product.thumbnail.url if item.product.thumbnail else None,
                'is_active': item.product.is_active,
                'stock_quantity': item.product.stock_quantity,
                'is_out_of_stock': item.product.is_out_of_stock
            },
            'added_at': item.created_at
        } for item in wishlist_items]
        
        return Response({
            'wishlist': data,
            'count': len(data)
        })
    
    def post(self, request):
        """Thêm sản phẩm vào danh sách yêu thích"""
        product_id = request.data.get('product_id')
        
        if not product_id:
            return Response({
                'detail': 'product_id là bắt buộc'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        product = get_object_or_404(ProductModel, id=product_id, is_active=True)
        
        # Kiểm tra đã tồn tại chưa
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if created:
            return Response({
                'detail': 'Đã thêm vào danh sách yêu thích',
                'wishlist_item': {
                    'id': wishlist_item.id,
                    'product_name': product.name
                }
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'detail': 'Sản phẩm đã có trong danh sách yêu thích'
            }, status=status.HTTP_200_OK)


class WishlistRemoveApi(APIView):
    """Xóa khỏi danh sách yêu thích"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, product_id):
        """Xóa sản phẩm khỏi wishlist"""
        wishlist_item = get_object_or_404(
            Wishlist,
            user=request.user,
            product_id=product_id
        )
        
        product_name = wishlist_item.product.name
        wishlist_item.delete()
        
        return Response({
            'detail': f'Đã xóa {product_name} khỏi danh sách yêu thích'
        })


class WishlistCheckApi(APIView):
    """Kiểm tra sản phẩm có trong wishlist không"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, product_id):
        """Kiểm tra sản phẩm có trong wishlist"""
        exists = Wishlist.objects.filter(
            user=request.user,
            product_id=product_id
        ).exists()
        
        return Response({
            'in_wishlist': exists,
            'product_id': product_id
        })