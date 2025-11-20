from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import TokenAuthentication
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import models

from payments.models import Payment
from payments.services import vnpay_service, momo_service
from orders.infrastructure.models import OrderModel


class VNPayCreatePaymentApi(APIView):
    """Tạo thanh toán VNPay"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Tạo URL thanh toán VNPay"""
        order_id = request.data.get('order_id')
        
        if not order_id:
            return Response({
                'detail': 'order_id là bắt buộc'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Lấy order
        order = get_object_or_404(OrderModel, id=order_id, buyer=request.user)
        
        # Kiểm tra đơn hàng đã có payment chưa
        payment, created = Payment.objects.get_or_create(
            order=order,
            defaults={
                'method': 'vnpay',
                'amount': order.total_vnd,
                'status': Payment.Status.PENDING
            }
        )
        
        if not created and payment.status == Payment.Status.PAID:
            return Response({
                'detail': 'Đơn hàng đã được thanh toán'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Cập nhật method nếu cần
        if payment.method != 'vnpay':
            payment.method = 'vnpay'
            payment.save()
        
        # Tạo payment URL
        order_info = f"Thanh toan don hang {order.id}"
        ip_addr = self._get_client_ip(request)
        
        payment_url, txn_ref = vnpay_service.create_payment_url(
            order_id=order.id,
            amount=order.total_vnd,
            order_info=order_info,
            ip_addr=ip_addr
        )
        
        # Lưu transaction ref
        payment.transaction_id = txn_ref
        payment.gateway_response = {'txn_ref': txn_ref}
        payment.save()
        
        return Response({
            'payment_url': payment_url,
            'payment_id': payment.id,
            'transaction_ref': txn_ref
        })
    
    def _get_client_ip(self, request):
        """Lấy IP của client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip


@method_decorator(csrf_exempt, name='dispatch')
class VNPayReturnView(APIView):
    """Xử lý callback từ VNPay"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """VNPay redirect về sau khi thanh toán"""
        query_params = dict(request.query_params)
        
        # Xác thực chữ ký
        is_valid, message = vnpay_service.verify_return_data(query_params)
        
        if not is_valid:
            return Response({
                'success': False,
                'message': message
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Lấy thông tin giao dịch
        txn_ref = query_params.get('vnp_TxnRef', '')
        vnp_transaction_no = query_params.get('vnp_TransactionNo', '')
        amount = int(query_params.get('vnp_Amount', 0)) // 100  # Chia 100 vì VNPay nhân 100
        
        # Tìm payment
        payment = Payment.objects.filter(transaction_id=txn_ref).first()
        
        if not payment:
            return Response({
                'success': False,
                'message': 'Không tìm thấy giao dịch'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Cập nhật trạng thái thanh toán
        if payment.status != Payment.Status.PAID:
            payment.mark_as_paid(
                transaction_id=vnp_transaction_no,
                gateway_response={
                    'vnp_data': query_params,
                    'verified': True
                }
            )
        
        # Redirect về frontend với thông tin
        frontend_url = f"http://127.0.0.1:8000/payment-success?order_id={payment.order.id}&payment_id={payment.id}"
        return redirect(frontend_url)


class MoMoCreatePaymentApi(APIView):
    """Tạo thanh toán MoMo"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Tạo thanh toán MoMo"""
        order_id = request.data.get('order_id')
        
        if not order_id:
            return Response({
                'detail': 'order_id là bắt buộc'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Lấy order
        order = get_object_or_404(OrderModel, id=order_id, buyer=request.user)
        
        # Kiểm tra đơn hàng đã có payment chưa
        payment, created = Payment.objects.get_or_create(
            order=order,
            defaults={
                'method': 'momo',
                'amount': order.total_vnd,
                'status': Payment.Status.PENDING
            }
        )
        
        if not created and payment.status == Payment.Status.PAID:
            return Response({
                'detail': 'Đơn hàng đã được thanh toán'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Cập nhật method nếu cần
        if payment.method != 'momo':
            payment.method = 'momo'
            payment.save()
        
        # Tạo thanh toán MoMo
        order_info = f"Thanh toan don hang {order.id} - CleanAgri"
        
        success, result, response_data = momo_service.create_payment(
            order_id=order.id,
            amount=order.total_vnd,
            order_info=order_info
        )
        
        if not success:
            return Response({
                'success': False,
                'message': result
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Lưu thông tin
        payment.gateway_response = response_data
        payment.save()
        
        return Response({
            'success': True,
            'pay_url': result,
            'payment_id': payment.id
        })


@method_decorator(csrf_exempt, name='dispatch')
class MoMoReturnView(APIView):
    """Xử lý callback từ MoMo"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """MoMo redirect về sau khi thanh toán"""
        query_params = dict(request.query_params)
        
        # Xác thực
        is_valid, message = momo_service.verify_ipn(query_params)
        
        if not is_valid:
            return Response({
                'success': False,
                'message': message
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Lấy thông tin
        order_id_str = query_params.get('orderId', '')
        trans_id = query_params.get('transId', '')
        
        # Extract order_id từ orderId (format: ORDER123)
        order_id = int(order_id_str.replace('ORDER', ''))
        
        # Tìm payment
        order = OrderModel.objects.filter(id=order_id).first()
        if not order:
            return Response({
                'success': False,
                'message': 'Không tìm thấy đơn hàng'
            }, status=status.HTTP_404_NOT_FOUND)
        
        payment = Payment.objects.filter(order=order).first()
        if not payment:
            return Response({
                'success': False,
                'message': 'Không tìm thấy giao dịch'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Cập nhật trạng thái
        if payment.status != Payment.Status.PAID:
            payment.mark_as_paid(
                transaction_id=trans_id,
                gateway_response={
                    'momo_data': query_params,
                    'verified': True
                }
            )
        
        # Redirect về frontend
        frontend_url = f"http://127.0.0.1:8000/payment-success?order_id={order.id}&payment_id={payment.id}"
        return redirect(frontend_url)


@method_decorator(csrf_exempt, name='dispatch')
class MoMoNotifyView(APIView):
    """Xử lý IPN (notify) từ MoMo"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """MoMo gửi IPN để thông báo kết quả thanh toán"""
        data = request.data
        
        # Xác thực
        is_valid, message = momo_service.verify_ipn(data)
        
        if not is_valid:
            return JsonResponse({
                'status': 'error',
                'message': message
            }, status=400)
        
        # Lấy thông tin
        order_id_str = data.get('orderId', '')
        trans_id = data.get('transId', '')
        result_code = int(data.get('resultCode', -1))
        
        # Extract order_id
        order_id = int(order_id_str.replace('ORDER', ''))
        
        # Tìm payment
        order = OrderModel.objects.filter(id=order_id).first()
        if order:
            payment = Payment.objects.filter(order=order).first()
            if payment and result_code == 0:
                # Cập nhật trạng thái nếu chưa paid
                if payment.status != Payment.Status.PAID:
                    payment.mark_as_paid(
                        transaction_id=trans_id,
                        gateway_response={
                            'momo_ipn': data,
                            'verified': True
                        }
                    )
        
        # Trả về response cho MoMo
        return JsonResponse({
            'status': 'success',
            'message': 'IPN received'
        })


class TestPaymentSuccessView(APIView):
    """Trang test hiển thị kết quả thanh toán"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Hiển thị kết quả thanh toán"""
        order_id = request.query_params.get('order_id')
        payment_id = request.query_params.get('payment_id')
        
        if not order_id or not payment_id:
            return Response({
                'success': False,
                'message': 'Thiếu thông tin'
            })
        
        order = get_object_or_404(OrderModel, id=order_id)
        payment = get_object_or_404(Payment, id=payment_id)
        
        return Response({
            'success': True,
            'message': 'Thanh toán thành công!',
            'order': {
                'id': order.id,
                'total_vnd': order.total_vnd,
                'status': order.get_status_display()
            },
            'payment': {
                'id': payment.id,
                'method': payment.get_method_display(),
                'status': payment.get_status_display(),
                'transaction_id': payment.transaction_id,
                'payment_date': payment.payment_date
            }
        })