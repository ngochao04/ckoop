from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import TokenAuthentication
from django.shortcuts import get_object_or_404
from django.utils import timezone

from payments.models import Payment, BankAccount, PaymentGatewayConfig
from orders.infrastructure.models import OrderModel


class PaymentMethodsApi(APIView):
    """Lấy danh sách phương thức thanh toán khả dụng"""
    
    def get(self, request):
        """Danh sách phương thức thanh toán"""
        # Phương thức cơ bản luôn có
        methods = [
            {
                'code': 'cod',
                'name': 'Thanh toán khi nhận hàng (COD)',
                'description': 'Thanh toán bằng tiền mặt khi nhận hàng',
                'icon': '💵',
                'is_available': True
            }
        ]
        
        # Chuyển khoản ngân hàng
        bank_accounts = BankAccount.objects.filter(is_active=True)
        if bank_accounts.exists():
            methods.append({
                'code': 'bank',
                'name': 'Chuyển khoản ngân hàng',
                'description': 'Chuyển khoản qua tài khoản ngân hàng',
                'icon': '🏦',
                'is_available': True,
                'bank_accounts': [{
                    'id': acc.id,
                    'bank_name': acc.bank_name,
                    'account_number': acc.account_number,
                    'account_holder': acc.account_holder,
                    'qr_code': acc.qr_code.url if acc.qr_code else None
                } for acc in bank_accounts]
            })
        
        # Các cổng thanh toán online
        gateways = PaymentGatewayConfig.objects.filter(is_active=True)
        for gateway in gateways:
            methods.append({
                'code': gateway.name,
                'name': gateway.display_name,
                'description': f'Thanh toán qua {gateway.display_name}',
                'icon': gateway.logo.url if gateway.logo else '💳',
                'is_available': True,
                'fees': {
                    'fixed': gateway.fixed_fee,
                    'percentage': float(gateway.percentage_fee)
                }
            })
        
        return Response({
            'payment_methods': methods
        })


class CreatePaymentApi(APIView):
    """Tạo thanh toán cho đơn hàng"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, order_id):
        """Tạo thanh toán cho đơn hàng"""
        order = get_object_or_404(
            OrderModel, 
            id=order_id, 
            buyer=request.user
        )
        
        # Kiểm tra đơn hàng đã có thanh toán chưa
        if hasattr(order, 'payment'):
            return Response({
                'detail': 'Đơn hàng đã có thông tin thanh toán',
                'payment': {
                    'id': order.payment.id,
                    'method': order.payment.get_method_display(),
                    'status': order.payment.get_status_display()
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Kiểm tra trạng thái đơn hàng
        if order.status not in [OrderModel.Status.NEW]:
            return Response({
                'detail': 'Đơn hàng không ở trạng thái cho phép thanh toán'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        method = request.data.get('method', 'cod')
        
        # Validate method
        valid_methods = dict(Payment.Method.choices).keys()
        if method not in valid_methods:
            return Response({
                'detail': f'Phương thức thanh toán không hợp lệ. Chọn: {list(valid_methods)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Tạo payment
        payment = Payment.objects.create(
            order=order,
            method=method,
            amount=order.total_vnd,
            status=Payment.Status.PENDING
        )
        
        response_data = {
            'detail': 'Tạo thanh toán thành công',
            'payment': {
                'id': payment.id,
                'order_id': order.id,
                'method': payment.get_method_display(),
                'amount': payment.amount,
                'status': payment.get_status_display(),
                'created_at': payment.created_at
            }
        }
        
        # Nếu là COD, tự động đánh dấu là pending
        if method == 'cod':
            response_data['message'] = 'Bạn sẽ thanh toán khi nhận hàng'
        
        # Nếu là bank transfer, trả về thông tin tài khoản
        elif method == 'bank':
            bank_accounts = BankAccount.objects.filter(is_active=True)
            response_data['bank_info'] = [{
                'bank_name': acc.bank_name,
                'account_number': acc.account_number,
                'account_holder': acc.account_holder,
                'qr_code': acc.qr_code.url if acc.qr_code else None
            } for acc in bank_accounts]
            response_data['message'] = 'Vui lòng chuyển khoản và cập nhật mã giao dịch'
        
        # Nếu là gateway khác (VNPay, MoMo, etc.)
        else:
            response_data['message'] = f'Đang chuyển đến cổng thanh toán {payment.get_method_display()}'
            # TODO: Tích hợp với payment gateway
        
        return Response(response_data, status=status.HTTP_201_CREATED)


class PaymentDetailApi(APIView):
    """Chi tiết thanh toán"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, payment_id):
        """Xem chi tiết thanh toán"""
        payment = get_object_or_404(Payment, id=payment_id)
        
        # Kiểm tra quyền
        if payment.order.buyer != request.user and not request.user.is_staff:
            return Response({
                'detail': 'Bạn không có quyền xem thanh toán này'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return Response({
            'id': payment.id,
            'order': {
                'id': payment.order.id,
                'total_vnd': payment.order.total_vnd,
                'status': payment.order.get_status_display()
            },
            'method': payment.get_method_display(),
            'status': payment.get_status_display(),
            'amount': payment.amount,
            'transaction_id': payment.transaction_id,
            'payment_date': payment.payment_date,
            'created_at': payment.created_at
        })


class ConfirmPaymentApi(APIView):
    """Xác nhận đã thanh toán (cho Bank Transfer)"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, payment_id):
        """Xác nhận đã chuyển khoản"""
        payment = get_object_or_404(Payment, id=payment_id)
        
        # Kiểm tra quyền
        if payment.order.buyer != request.user:
            return Response({
                'detail': 'Bạn không có quyền thực hiện thao tác này'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Chỉ cho phép xác nhận với bank transfer
        if payment.method != 'bank':
            return Response({
                'detail': 'Chỉ áp dụng cho thanh toán chuyển khoản'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Kiểm tra trạng thái
        if payment.status != Payment.Status.PENDING:
            return Response({
                'detail': f'Không thể xác nhận thanh toán ở trạng thái {payment.get_status_display()}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        transaction_id = request.data.get('transaction_id', '')
        note = request.data.get('note', '')
        
        if not transaction_id:
            return Response({
                'detail': 'Vui lòng cung cấp mã giao dịch'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Lưu thông tin xác nhận
        payment.transaction_id = transaction_id
        payment.gateway_response = {
            'user_confirmed': True,
            'note': note,
            'confirmed_at': timezone.now().isoformat()
        }
        payment.save()
        
        return Response({
            'detail': 'Đã ghi nhận thông tin thanh toán. Admin sẽ kiểm tra và xác nhận.',
            'payment': {
                'id': payment.id,
                'transaction_id': payment.transaction_id,
                'status': payment.get_status_display()
            }
        })


class AdminVerifyPaymentApi(APIView):
    """[ADMIN] Xác minh thanh toán"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, payment_id):
        """Admin xác minh đã nhận được tiền"""
        if not request.user.is_staff:
            return Response({
                'detail': 'Bạn không có quyền thực hiện thao tác này'
            }, status=status.HTTP_403_FORBIDDEN)
        
        payment = get_object_or_404(Payment, id=payment_id)
        
        action = request.data.get('action', 'approve')  # approve | reject
        
        if action == 'approve':
            payment.mark_as_paid(
                transaction_id=payment.transaction_id,
                gateway_response={
                    'admin_verified': True,
                    'verified_by': request.user.username,
                    'verified_at': timezone.now().isoformat()
                }
            )
            
            return Response({
                'detail': 'Đã xác nhận thanh toán thành công',
                'payment': {
                    'id': payment.id,
                    'status': payment.get_status_display(),
                    'payment_date': payment.payment_date
                }
            })
        
        elif action == 'reject':
            payment.status = Payment.Status.FAILED
            payment.gateway_response = {
                'admin_rejected': True,
                'rejected_by': request.user.username,
                'rejected_at': timezone.now().isoformat(),
                'reason': request.data.get('reason', '')
            }
            payment.save()
            
            return Response({
                'detail': 'Đã từ chối thanh toán',
                'payment': {
                    'id': payment.id,
                    'status': payment.get_status_display()
                }
            })
        
        return Response({
            'detail': 'Action không hợp lệ. Chọn: approve hoặc reject'
        }, status=status.HTTP_400_BAD_REQUEST)


class AdminPendingPaymentsApi(APIView):
    """[ADMIN] Danh sách thanh toán chờ xác minh"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Lấy danh sách thanh toán chờ xác minh"""
        if not request.user.is_staff:
            return Response({
                'detail': 'Bạn không có quyền thực hiện thao tác này'
            }, status=status.HTTP_403_FORBIDDEN)
        
        payments = Payment.objects.filter(
            method='bank',
            status=Payment.Status.PENDING
        ).select_related('order', 'order__buyer').order_by('-created_at')
        
        data = [{
            'id': p.id,
            'order_id': p.order.id,
            'buyer': {
                'username': p.order.buyer.username,
                'email': p.order.buyer.email
            },
            'amount': p.amount,
            'transaction_id': p.transaction_id,
            'gateway_response': p.gateway_response,
            'created_at': p.created_at
        } for p in payments]
        
        return Response({
            'pending_payments': data,
            'count': len(data)
        })


class MyPaymentsApi(APIView):
    """Danh sách thanh toán của tôi"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Lấy danh sách thanh toán của user"""
        payments = Payment.objects.filter(
            order__buyer=request.user
        ).select_related('order').order_by('-created_at')
        
        data = [{
            'id': p.id,
            'order_id': p.order.id,
            'method': p.get_method_display(),
            'status': p.get_status_display(),
            'amount': p.amount,
            'transaction_id': p.transaction_id,
            'payment_date': p.payment_date,
            'created_at': p.created_at
        } for p in payments]
        
        return Response({
            'payments': data,
            'count': len(data)
        })