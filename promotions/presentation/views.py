from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import TokenAuthentication
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

from promotions.models import Voucher, VoucherUsage, FlashSale, FlashSaleProduct


class PublicVouchersApi(APIView):
    """Danh sách voucher công khai"""
    
    def get(self, request):
        """Lấy voucher công khai đang hoạt động"""
        now = timezone.now()
        
        vouchers = Voucher.objects.filter(
            is_active=True,
            is_public=True,
            start_date__lte=now,
            end_date__gte=now
        ).order_by('-created_at')
        
        data = [{
            'id': v.id,
            'code': v.code,
            'name': v.name,
            'description': v.description,
            'discount_type': v.discount_type,
            'discount_type_display': v.get_discount_type_display(),
            'discount_value': v.discount_value,
            'max_discount': v.max_discount if v.discount_type == 'percentage' else None,
            'min_order_value': v.min_order_value,
            'remaining_quantity': v.remaining_quantity,
            'end_date': v.end_date,
            'usage_limit_per_user': v.usage_limit_per_user
        } for v in vouchers]
        
        return Response({
            'vouchers': data,
            'count': len(data)
        })


class CheckVoucherApi(APIView):
    """Kiểm tra voucher có hợp lệ không"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Kiểm tra voucher"""
        code = request.data.get('code', '').strip().upper()
        order_value = int(request.data.get('order_value', 0))
        
        if not code:
            return Response({
                'valid': False,
                'message': 'Vui lòng nhập mã voucher'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            voucher = Voucher.objects.get(code=code)
        except Voucher.DoesNotExist:
            return Response({
                'valid': False,
                'message': 'Mã voucher không tồn tại'
            })
        
        # Kiểm tra có thể sử dụng không
        can_use, message = voucher.can_use(request.user, order_value)
        
        if not can_use:
            return Response({
                'valid': False,
                'message': message
            })
        
        # Tính số tiền được giảm
        discount_amount = voucher.calculate_discount(order_value)
        final_price = order_value - discount_amount
        
        return Response({
            'valid': True,
            'message': 'Áp dụng voucher thành công',
            'voucher': {
                'id': voucher.id,
                'code': voucher.code,
                'name': voucher.name,
                'discount_type': voucher.get_discount_type_display()
            },
            'discount_amount': discount_amount,
            'final_price': final_price
        })


class MyVoucherUsageApi(APIView):
    """Lịch sử sử dụng voucher của tôi"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Xem lịch sử sử dụng voucher"""
        usages = VoucherUsage.objects.filter(
            user=request.user
        ).select_related('voucher', 'order').order_by('-used_at')
        
        data = [{
            'id': u.id,
            'voucher_code': u.voucher.code,
            'voucher_name': u.voucher.name,
            'order_id': u.order.id,
            'discount_amount': u.discount_amount,
            'used_at': u.used_at
        } for u in usages]
        
        return Response({
            'usage_history': data,
            'count': len(data)
        })


class ActiveFlashSalesApi(APIView):
    """Danh sách Flash Sale đang diễn ra"""
    
    def get(self, request):
        """Lấy flash sale đang hoạt động"""
        now = timezone.now()
        
        flash_sales = FlashSale.objects.filter(
            is_active=True,
            start_time__lte=now,
            end_time__gte=now
        ).prefetch_related('products')
        
        data = []
        for fs in flash_sales:
            products = FlashSaleProduct.objects.filter(
                flash_sale=fs
            ).select_related('product')[:20]
            
            data.append({
                'id': fs.id,
                'name': fs.name,
                'description': fs.description,
                'discount_percentage': fs.discount_percentage,
                'start_time': fs.start_time,
                'end_time': fs.end_time,
                'time_remaining': fs.time_remaining(),
                'products': [{
                    'id': fsp.product.id,
                    'name': fsp.product.name,
                    'original_price': fsp.original_price,
                    'sale_price': fsp.sale_price,
                    'discount_percentage': fsp.discount_percentage,
                    'thumbnail': fsp.product.thumbnail.url if fsp.product.thumbnail else None,
                    'quantity_limit': fsp.quantity_limit,
                    'sold_quantity': fsp.sold_quantity,
                    'is_available': fsp.is_available()
                } for fsp in products]
            })
        
        return Response({
            'flash_sales': data,
            'count': len(data)
        })


class FlashSaleDetailApi(APIView):
    """Chi tiết Flash Sale"""
    
    def get(self, request, flash_sale_id):
        """Xem chi tiết flash sale"""
        flash_sale = get_object_or_404(FlashSale, id=flash_sale_id)
        
        if not flash_sale.is_running():
            return Response({
                'detail': 'Flash sale không còn hoạt động hoặc đã kết thúc'
            }, status=status.HTTP_404_NOT_FOUND)
        
        products = FlashSaleProduct.objects.filter(
            flash_sale=flash_sale
        ).select_related('product')
        
        return Response({
            'id': flash_sale.id,
            'name': flash_sale.name,
            'description': flash_sale.description,
            'discount_percentage': flash_sale.discount_percentage,
            'start_time': flash_sale.start_time,
            'end_time': flash_sale.end_time,
            'time_remaining': flash_sale.time_remaining(),
            'products': [{
                'id': fsp.product.id,
                'name': fsp.product.name,
                'slug': fsp.product.slug,
                'original_price': fsp.original_price,
                'sale_price': fsp.sale_price,
                'discount_percentage': fsp.discount_percentage,
                'thumbnail': fsp.product.thumbnail.url if fsp.product.thumbnail else None,
                'quantity_limit': fsp.quantity_limit,
                'sold_quantity': fsp.sold_quantity,
                'is_available': fsp.is_available(),
                'stock_quantity': fsp.product.stock_quantity
            } for fsp in products],
            'total_products': products.count()
        })


class UpcomingFlashSalesApi(APIView):
    """Flash Sale sắp diễn ra"""
    
    def get(self, request):
        """Lấy flash sale sắp diễn ra"""
        now = timezone.now()
        
        upcoming = FlashSale.objects.filter(
            is_active=True,
            start_time__gt=now
        ).order_by('start_time')[:5]
        
        data = [{
            'id': fs.id,
            'name': fs.name,
            'description': fs.description,
            'discount_percentage': fs.discount_percentage,
            'start_time': fs.start_time,
            'end_time': fs.end_time,
            'time_until_start': int((fs.start_time - now).total_seconds()),
            'product_count': fs.products.count()
        } for fs in upcoming]
        
        return Response({
            'upcoming_flash_sales': data,
            'count': len(data)
        })


# ============= ADMIN APIs =============

class AdminVoucherListApi(APIView):
    """[ADMIN] Quản lý voucher"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Danh sách tất cả voucher"""
        if not request.user.is_staff:
            return Response({
                'detail': 'Bạn không có quyền thực hiện thao tác này'
            }, status=status.HTTP_403_FORBIDDEN)
        
        status_filter = request.query_params.get('status', 'all')
        
        vouchers = Voucher.objects.all()
        
        if status_filter == 'active':
            now = timezone.now()
            vouchers = vouchers.filter(
                is_active=True,
                start_date__lte=now,
                end_date__gte=now
            )
        elif status_filter == 'expired':
            vouchers = vouchers.filter(end_date__lt=timezone.now())
        elif status_filter == 'upcoming':
            vouchers = vouchers.filter(start_date__gt=timezone.now())
        
        vouchers = vouchers.order_by('-created_at')
        
        data = [{
            'id': v.id,
            'code': v.code,
            'name': v.name,
            'discount_type': v.get_discount_type_display(),
            'discount_value': v.discount_value,
            'min_order_value': v.min_order_value,
            'used_quantity': v.used_quantity,
            'total_quantity': v.total_quantity,
            'remaining_quantity': v.remaining_quantity,
            'is_active': v.is_active,
            'is_public': v.is_public,
            'start_date': v.start_date,
            'end_date': v.end_date,
            'is_valid': v.is_valid()[0]
        } for v in vouchers]
        
        return Response({
            'vouchers': data,
            'count': len(data)
        })


class AdminVoucherStatsApi(APIView):
    """[ADMIN] Thống kê voucher"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, voucher_id):
        """Thống kê sử dụng voucher"""
        if not request.user.is_staff:
            return Response({
                'detail': 'Bạn không có quyền thực hiện thao tác này'
            }, status=status.HTTP_403_FORBIDDEN)
        
        voucher = get_object_or_404(Voucher, id=voucher_id)
        
        usages = VoucherUsage.objects.filter(voucher=voucher)
        
        total_usage = usages.count()
        total_discount = sum(u.discount_amount for u in usages)
        
        # Top users
        from django.db.models import Count, Sum
        top_users = usages.values(
            'user__username', 'user__email'
        ).annotate(
            usage_count=Count('id'),
            total_discount=Sum('discount_amount')
        ).order_by('-usage_count')[:10]
        
        return Response({
            'voucher': {
                'id': voucher.id,
                'code': voucher.code,
                'name': voucher.name
            },
            'stats': {
                'total_usage': total_usage,
                'total_discount': total_discount,
                'remaining_quantity': voucher.remaining_quantity,
                'usage_rate': f"{(voucher.used_quantity / voucher.total_quantity * 100):.1f}%" if voucher.total_quantity > 0 else "N/A"
            },
            'top_users': list(top_users)
        })