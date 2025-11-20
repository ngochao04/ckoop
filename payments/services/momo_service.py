import hashlib
import hmac
import json
import requests
import os
from typing import Dict, Tuple


class MoMoService:
    """Service xử lý thanh toán MoMo"""
    
    def __init__(self):
        self.partner_code = os.getenv('MOMO_PARTNER_CODE', '')
        self.access_key = os.getenv('MOMO_ACCESS_KEY', '')
        self.secret_key = os.getenv('MOMO_SECRET_KEY', '')
        self.endpoint = os.getenv('MOMO_ENDPOINT', '')
        self.return_url = os.getenv('MOMO_RETURN_URL', '')
        self.notify_url = os.getenv('MOMO_NOTIFY_URL', '')
    
    def _create_signature(self, raw_data: str) -> str:
        """Tạo chữ ký HMAC SHA256"""
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            raw_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def create_payment(
        self, 
        order_id: int, 
        amount: int, 
        order_info: str
    ) -> Tuple[bool, str, Dict]:
        """
        Tạo thanh toán MoMo
        
        Args:
            order_id: ID đơn hàng
            amount: Số tiền (VND)
            order_info: Thông tin đơn hàng
        
        Returns:
            (success, pay_url or error_message, response_data)
        """
        # Tạo request ID unique
        from datetime import datetime
        request_id = f"CLEANAGRI{order_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        order_id_str = f"ORDER{order_id}"
        
        # Chuẩn bị data
        request_data = {
            "partnerCode": self.partner_code,
            "accessKey": self.access_key,
            "requestId": request_id,
            "amount": str(amount),
            "orderId": order_id_str,
            "orderInfo": order_info,
            "returnUrl": self.return_url,
            "notifyUrl": self.notify_url,
            "extraData": "",  # Có thể truyền thêm data
            "requestType": "captureWallet",  # hoặc "payWithATM"
            "signature": ""
        }
        
        # Tạo raw signature
        raw_signature = (
            f"accessKey={self.access_key}"
            f"&amount={amount}"
            f"&extraData="
            f"&notifyUrl={self.notify_url}"
            f"&orderId={order_id_str}"
            f"&orderInfo={order_info}"
            f"&partnerCode={self.partner_code}"
            f"&redirectUrl={self.return_url}"
            f"&requestId={request_id}"
            f"&requestType=captureWallet"
        )
        
        # Tạo chữ ký
        request_data['signature'] = self._create_signature(raw_signature)
        
        try:
            # Gọi API MoMo
            response = requests.post(
                self.endpoint,
                json=request_data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            result = response.json()
            
            # Kiểm tra kết quả
            if result.get('errorCode') == 0:
                pay_url = result.get('payUrl', '')
                return True, pay_url, result
            else:
                error_message = result.get('message', 'Lỗi không xác định')
                return False, error_message, result
        
        except requests.exceptions.RequestException as e:
            return False, f"Lỗi kết nối MoMo: {str(e)}", {}
        except Exception as e:
            return False, f"Lỗi: {str(e)}", {}
    
    def verify_ipn(self, data: Dict) -> Tuple[bool, str]:
        """
        Xác thực IPN (Instant Payment Notification) từ MoMo
        
        Returns:
            (is_valid, message)
        """
        # Lấy signature từ data
        received_signature = data.get('signature', '')
        
        # Tạo raw signature để verify
        raw_signature = (
            f"accessKey={data.get('accessKey', '')}"
            f"&amount={data.get('amount', '')}"
            f"&extraData={data.get('extraData', '')}"
            f"&message={data.get('message', '')}"
            f"&orderId={data.get('orderId', '')}"
            f"&orderInfo={data.get('orderInfo', '')}"
            f"&orderType={data.get('orderType', '')}"
            f"&partnerCode={data.get('partnerCode', '')}"
            f"&payType={data.get('payType', '')}"
            f"&requestId={data.get('requestId', '')}"
            f"&responseTime={data.get('responseTime', '')}"
            f"&resultCode={data.get('resultCode', '')}"
            f"&transId={data.get('transId', '')}"
        )
        
        # Tạo chữ ký để so sánh
        calculated_signature = self._create_signature(raw_signature)
        
        # So sánh
        if calculated_signature != received_signature:
            return False, "Chữ ký không hợp lệ"
        
        # Kiểm tra result code
        result_code = int(data.get('resultCode', -1))
        
        if result_code == 0:
            return True, "Giao dịch thành công"
        else:
            return False, self._get_error_message(result_code)
    
    def _get_error_message(self, code: int) -> str:
        """Lấy message từ result code"""
        messages = {
            0: 'Giao dịch thành công',
            9000: 'Giao dịch đã được xác nhận thành công',
            1000: 'Giao dịch đã được khởi tạo, chờ người dùng xác nhận thanh toán',
            1001: 'Giao dịch thất bại do người dùng từ chối thanh toán',
            1002: 'Giao dịch thất bại do tài khoản người dùng không đủ tiền',
            1003: 'Giao dịch bị từ chối bởi nhà phát hành tài khoản người dùng',
            1004: 'Giao dịch thất bại do số tiền thanh toán vượt quá hạn mức thanh toán',
            1005: 'Giao dịch thất bại do url hoặc QR code đã hết hạn',
            1006: 'Giao dịch thất bại do người dùng đã từ chối xác nhận thanh toán',
            1007: 'Giao dịch bị từ chối vì tài khoản người dùng đang bị tạm khóa',
            1026: 'Giao dịch bị hạn chế theo thể lệ chương trình khuyến mại',
            1080: 'Giao dịch hoàn tiền bị từ chối',
            1081: 'Giao dịch hoàn tiền đang được xử lý',
            2001: 'Giao dịch thất bại do sai thông tin',
            3001: 'Giao dịch bị từ chối bởi MoMo',
            3002: 'Giao dịch thất bại do thông tin đơn hàng không hợp lệ',
            3003: 'Giao dịch thất bại do số tiền thanh toán không hợp lệ',
            3004: 'Giao dịch thất bại do vượt quá số tiền thanh toán',
            4001: 'Giao dịch thất bại do lỗi hệ thống'
        }
        return messages.get(code, f'Lỗi không xác định (Code: {code})')


# Singleton instance
momo_service = MoMoService()