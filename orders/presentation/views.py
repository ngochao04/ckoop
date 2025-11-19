from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import TokenAuthentication
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta

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
        
        # Nếu là admin, cho phép xem tất cả đơn hàng
        if user.is_staff:
            order = OrderModel.objects.filter(id=order_id).prefetch_related('lines').first()
        else:
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
            'buyer': {
                'id': order.buyer.id,
                'username': order.buyer.username,
                'email': order.buyer.email
            },
            'total_vnd': order.total_vnd,
            'status': order.status,
            'status_display': order.get_status_display(),
            'created_at': order.created_at,
            'lines': lines
        })


class CancelOrderApi(APIView):
    """Hủy đơn hàng"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, order_id):
        user = request.user
        order = get_object_or_404(OrderModel, id=order_id, buyer=user)
        
        # Chỉ cho phép hủy đơn hàng mới
        if order.status != OrderModel.Status.NEW:
            return Response({
                'detail': f'Không thể hủy đơn hàng ở trạng thái {order.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = OrderModel.Status.CANCEL
        order.save()
        
        return Response({
            'detail': 'Đã hủy đơn hàng thành công',
            'order_id': order.id
        })


# ============= ADMIN APIs =============

class AdminAllOrdersApi(APIView):
    """[ADMIN] Xem tất cả đơn hàng"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        if not request.user.is_staff:
            return Response({
                'detail': 'Bạn không có quyền thực hiện thao tác này'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Lọc theo trạng thái
        status_filter = request.query_params.get('status')
        search = request.query_params.get('search', '')
        
        orders = OrderModel.objects.select_related('buyer').order_by('-created_at')
        
        if status_filter:
            orders = orders.filter(status=status_filter)
        
        if search:
            orders = orders.filter(
                Q(buyer__username__icontains=search) |
                Q(buyer__email__icontains=search) |
                Q(id__icontains=search)
            )
        
        # Phân trang đơn giản
        page = int(request.query_params.get('page', 1))
        per_page = 20
        start = (page - 1) * per_page
        end = start + per_page
        
        total = orders.count()
        orders_page = orders[start:end]
        
        data = [{
            'order_id': o.id,
            'buyer': {
                'id': o.buyer.id,
                'username': o.buyer.username,
                'email': o.buyer.email
            },
            'total_vnd': o.total_vnd,
            'status': o.status,
            'status_display': o.get_status_display(),
            'created_at': o.created_at,
            'items_count': o.lines.count()
        } for o in orders_page]
        
        return Response({
            'orders': data,
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
        })


class AdminUpdateOrderStatusApi(APIView):
    """[ADMIN] Cập nhật trạng thái đơn hàng"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, order_id):
        if not request.user.is_staff:
            return Response({
                'detail': 'Bạn không có quyền thực hiện thao tác này'
            }, status=status.HTTP_403_FORBIDDEN)
        
        order = get_object_or_404(OrderModel, id=order_id)
        new_status = request.data.get('status')
        
        if not new_status or new_status not in dict(OrderModel.Status.choices):
            return Response({
                'detail': 'Trạng thái không hợp lệ',
                'valid_statuses': list(dict(OrderModel.Status.choices).keys())
            }, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = new_status
        order.save()
        
        return Response({
            'detail': 'Đã cập nhật trạng thái đơn hàng',
            'order_id': order.id,
            'status': order.status,
            'status_display': order.get_status_display()
        })


class AdminDashboardApi(APIView):
    """[ADMIN] Dashboard thống kê tổng quan"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        if not request.user.is_staff:
            return Response({
                'detail': 'Bạn không có quyền thực hiện thao tác này'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Thống kê tổng quan
        total_orders = OrderModel.objects.count()
        total_revenue = OrderModel.objects.filter(
            status__in=[OrderModel.Status.PAID, OrderModel.Status.SHIP, OrderModel.Status.DONE]
        ).aggregate(total=Sum('total_vnd'))['total'] or 0
        
        # Đơn hàng theo trạng thái
        orders_by_status = {}
        for status_code, status_name in OrderModel.Status.choices:
            count = OrderModel.objects.filter(status=status_code).count()
            orders_by_status[status_code] = {
                'name': status_name,
                'count': count
            }
        
        # Doanh thu 7 ngày gần nhất
        today = timezone.now().date()
        revenue_last_7days = []
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            revenue = OrderModel.objects.filter(
                created_at__date=date,
                status__in=[OrderModel.Status.PAID, OrderModel.Status.SHIP, OrderModel.Status.DONE]
            ).aggregate(total=Sum('total_vnd'))['total'] or 0
            
            revenue_last_7days.append({
                'date': date.isoformat(),
                'revenue': revenue
            })
        
        # Đơn hàng mới nhất
        recent_orders = OrderModel.objects.select_related('buyer').order_by('-created_at')[:5]
        recent_orders_data = [{
            'order_id': o.id,
            'buyer': o.buyer.username,
            'total_vnd': o.total_vnd,
            'status': o.get_status_display(),
            'created_at': o.created_at
        } for o in recent_orders]
        
        # Sản phẩm bán chạy (top 5)
        from orders.infrastructure.models import OrderLineModel
        from django.db.models import Sum as DbSum
        
        top_products = OrderLineModel.objects.values(
            'product_name', 'sku'
        ).annotate(
            total_qty=DbSum('qty'),
            total_revenue=DbSum('price_vnd') * DbSum('qty')
        ).order_by('-total_qty')[:5]
        
        top_products_data = list(top_products)
        
        return Response({
            'overview': {
                'total_orders': total_orders,
                'total_revenue': total_revenue,
                'orders_by_status': orders_by_status
            },
            'revenue_last_7days': revenue_last_7days,
            'recent_orders': recent_orders_data,
            'top_products': top_products_data
        })


class AdminCustomersApi(APIView):
    """[ADMIN] Danh sách khách hàng"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        if not request.user.is_staff:
            return Response({
                'detail': 'Bạn không có quyền thực hiện thao tác này'
            }, status=status.HTTP_403_FORBIDDEN)
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        search = request.query_params.get('search', '')
        
        customers = User.objects.filter(is_customer=True)
        
        if search:
            customers = customers.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search)
            )
        
        customers = customers.order_by('-date_joined')
        
        # Phân trang
        page = int(request.query_params.get('page', 1))
        per_page = 20
        start = (page - 1) * per_page
        end = start + per_page
        
        total = customers.count()
        customers_page = customers[start:end]
        
        data = []
        for c in customers_page:
            orders = OrderModel.objects.filter(buyer=c)
            total_spent = orders.filter(
                status__in=[OrderModel.Status.PAID, OrderModel.Status.SHIP, OrderModel.Status.DONE]
            ).aggregate(total=Sum('total_vnd'))['total'] or 0
            
            data.append({
                'user_id': c.id,
                'username': c.username,
                'email': c.email,
                'phone': c.phone,
                'is_farmer': c.is_farmer,
                'date_joined': c.date_joined,
                'total_orders': orders.count(),
                'total_spent': total_spent
            })
        
        return Response({
            'customers': data,
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
        })