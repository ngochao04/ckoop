from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import TokenAuthentication
from orders.application.services import OrderService, CheckoutInput
from orders.infrastructure.models import OrderModel


class CheckoutApi(APIView):
    """Checkout - tạo đơn hàng từ giỏ hàng"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        try:
            order_id = OrderService().checkout(CheckoutInput(user_id=user.id))
            return Response({
                'detail': 'Đặt hàng thành công',
                'order_id': order_id
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({
                'detail': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class MyOrdersApi(APIView):
    """Danh sách đơn hàng của tôi"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        orders = OrderModel.objects.filter(buyer=user).order_by('-created_at')
        
        data = [{
            'order_id': o.id,
            'total_vnd': o.total_vnd,
            'status': o.status,
            'status_display': o.get_status_display(),
            'created_at': o.created_at,
            'items_count': o.lines.count()
        } for o in orders]
        
        return Response({'orders': data})


class OrderDetailApi(APIView):
    """Chi tiết đơn hàng"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, order_id):
        user = request.user
        order = OrderModel.objects.filter(
            id=order_id, 
            buyer=user
        ).prefetch_related('lines').first()
        
        if not order:
            return Response({
                'detail': 'Đơn hàng không tồn tại'
            }, status=status.HTTP_404_NOT_FOUND)
        
        lines = [{
            'product_name': line.product_name,
            'sku': line.sku,
            'price_vnd': line.price_vnd,
            'qty': line.qty,
            'line_total': line.price_vnd * line.qty
        } for line in order.lines.all()]
        
        return Response({
            'order_id': order.id,
            'total_vnd': order.total_vnd,
            'status': order.status,
            'status_display': order.get_status_display(),
            'created_at': order.created_at,
            'lines': lines
        })