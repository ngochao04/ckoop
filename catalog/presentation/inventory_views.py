from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import TokenAuthentication
from django.shortcuts import get_object_or_404
from django.db.models import Sum

from catalog.infrastructure.models import ProductModel, InventoryLog


class InventoryStockApi(APIView):
    """[ADMIN] Quản lý tồn kho"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Xem tồn kho tất cả sản phẩm"""
        if not request.user.is_staff:
            return Response({
                'detail': 'Bạn không có quyền thực hiện thao tác này'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Lọc
        filter_type = request.query_params.get('filter', 'all')
        search = request.query_params.get('search', '')
        
        products = ProductModel.objects.filter(is_active=True)
        
        if search:
            products = products.filter(name__icontains=search)
        
        # Lọc theo tình trạng kho
        if filter_type == 'low_stock':
            products = [p for p in products if p.is_low_stock and not p.is_out_of_stock]
        elif filter_type == 'out_of_stock':
            products = [p for p in products if p.is_out_of_stock]
        
        data = [{
            'id': p.id,
            'name': p.name,
            'sku': p.sku,
            'stock_quantity': p.stock_quantity,
            'low_stock_threshold': p.low_stock_threshold,
            'is_low_stock': p.is_low_stock,
            'is_out_of_stock': p.is_out_of_stock,
            'unit': p.unit,
            'price_vnd': p.price_vnd,
        } for p in products]
        
        return Response({
            'products': data,
            'count': len(data),
            'summary': {
                'total_products': ProductModel.objects.filter(is_active=True).count(),
                'low_stock_count': sum(1 for p in ProductModel.objects.filter(is_active=True) if p.is_low_stock),
                'out_of_stock_count': sum(1 for p in ProductModel.objects.filter(is_active=True) if p.is_out_of_stock),
            }
        })


class InventoryAdjustApi(APIView):
    """[ADMIN] Điều chỉnh tồn kho"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, product_id):
        """Điều chỉnh tồn kho cho sản phẩm"""
        if not request.user.is_staff:
            return Response({
                'detail': 'Bạn không có quyền thực hiện thao tác này'
            }, status=status.HTTP_403_FORBIDDEN)
        
        product = get_object_or_404(ProductModel, id=product_id)
        
        action = request.data.get('action')  # 'in', 'out', 'adjust'
        quantity = int(request.data.get('quantity', 0))
        note = request.data.get('note', '')
        
        if action not in ['in', 'out', 'adjust']:
            return Response({
                'detail': 'Action không hợp lệ. Chỉ chấp nhận: in, out, adjust'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if quantity <= 0 and action != 'adjust':
            return Response({
                'detail': 'Số lượng phải lớn hơn 0'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        previous_stock = product.stock_quantity
        
        try:
            if action == 'in':
                product.increase_stock(quantity)
                new_stock = product.stock_quantity
            elif action == 'out':
                product.reduce_stock(quantity)
                new_stock = product.stock_quantity
            else:  # adjust - đặt lại số lượng cụ thể
                new_quantity = int(request.data.get('new_quantity', 0))
                if new_quantity < 0:
                    return Response({
                        'detail': 'Số lượng mới không được âm'
                    }, status=status.HTTP_400_BAD_REQUEST)
                product.stock_quantity = new_quantity
                product.save()
                new_stock = new_quantity
                quantity = new_stock - previous_stock
            
            # Ghi log
            InventoryLog.objects.create(
                product=product,
                action=action,
                quantity=quantity,
                previous_stock=previous_stock,
                new_stock=new_stock,
                note=note,
                created_by=request.user
            )
            
            return Response({
                'detail': 'Cập nhật tồn kho thành công',
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'previous_stock': previous_stock,
                    'new_stock': new_stock,
                    'is_low_stock': product.is_low_stock,
                    'is_out_of_stock': product.is_out_of_stock
                }
            })
        
        except ValueError as e:
            return Response({
                'detail': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class InventoryLogApi(APIView):
    """[ADMIN] Xem lịch sử xuất nhập kho"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Lấy lịch sử xuất nhập kho"""
        if not request.user.is_staff:
            return Response({
                'detail': 'Bạn không có quyền thực hiện thao tác này'
            }, status=status.HTTP_403_FORBIDDEN)
        
        product_id = request.query_params.get('product_id')
        action = request.query_params.get('action')
        
        logs = InventoryLog.objects.select_related('product', 'created_by').all()
        
        if product_id:
            logs = logs.filter(product_id=product_id)
        
        if action:
            logs = logs.filter(action=action)
        
        # Phân trang
        page = int(request.query_params.get('page', 1))
        per_page = 50
        start = (page - 1) * per_page
        end = start + per_page
        
        total = logs.count()
        logs_page = logs[start:end]
        
        data = [{
            'id': log.id,
            'product': {
                'id': log.product.id,
                'name': log.product.name,
                'sku': log.product.sku
            },
            'action': log.action,
            'action_display': log.get_action_display(),
            'quantity': log.quantity,
            'previous_stock': log.previous_stock,
            'new_stock': log.new_stock,
            'note': log.note,
            'created_by': log.created_by.username if log.created_by else 'System',
            'created_at': log.created_at
        } for log in logs_page]
        
        return Response({
            'logs': data,
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
        })


class LowStockAlertApi(APIView):
    """[ADMIN] Cảnh báo sắp hết hàng"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Danh sách sản phẩm sắp hết hàng"""
        if not request.user.is_staff:
            return Response({
                'detail': 'Bạn không có quyền thực hiện thao tác này'
            }, status=status.HTTP_403_FORBIDDEN)
        
        products = ProductModel.objects.filter(is_active=True)
        
        low_stock = [p for p in products if p.is_low_stock and not p.is_out_of_stock]
        out_of_stock = [p for p in products if p.is_out_of_stock]
        
        return Response({
            'low_stock': [{
                'id': p.id,
                'name': p.name,
                'sku': p.sku,
                'stock_quantity': p.stock_quantity,
                'low_stock_threshold': p.low_stock_threshold
            } for p in low_stock],
            'out_of_stock': [{
                'id': p.id,
                'name': p.name,
                'sku': p.sku,
                'stock_quantity': p.stock_quantity
            } for p in out_of_stock],
            'summary': {
                'low_stock_count': len(low_stock),
                'out_of_stock_count': len(out_of_stock)
            }
        })