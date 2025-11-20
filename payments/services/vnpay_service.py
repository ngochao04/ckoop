import hashlib
import hmac
import urllib.parse
from datetime import datetime
from typing import Dict, Tuple
import os


class VNPayService:
    """Service xử lý thanh toán VNPay"""
    
    def __init__(self):
        self.tmn_code = os.getenv('VNPAY_TMN_CODE', '')
        self.secret_key = os.getenv('VNPAY_HASH_SECRET', '')
        self.vnpay_url = os.getenv('VNPAY_URL', '')
        self.return_url = os.getenv('VNPAY_RETURN_URL', '')
    
    def _create_signature(self, data: Dict[str, str]) -> str:
        """Tạo chữ ký bảo mật"""
        # Sắp xếp theo key
        sorted_data = sorted(data.items())
        
        # Tạo query string
        query_string = '&'.join([f"{k}={v}" for k, v in sorted_data])
        
        # Tạo HMAC SHA512
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        return signature
    
    def create_payment_url(
        self, 
        order_id: int, 
        amount: int, 
        order_info: str,
        ip_addr: str = '127.0.0.1'
    ) -> Tuple[str, str]:
        """
        Tạo URL thanh toán VNPay
        
        Args:
            order_id: ID đơn hàng
            amount: Số tiền (VND)
            order_info: Thông tin đơn hàng
            ip_addr: IP người dùng
        
        Returns:
            (payment_url, txn_ref)
        """
        # Tạo mã giao dịch (txnRef) - unique
        txn_ref = f"ORDER{order_id}"
        
        # Thời gian tạo (yyyyMMddHHmmss)
        create_date = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Làm sạch order_info - chỉ giữ chữ và số, không dấu
        clean_order_info = f"Thanh toan don hang {order_id}"
        
        # Chuẩn bị data (KHÔNG BAO GỒM vnp_SecureHash)
        vnpay_data = {
            'vnp_Version': '2.1.0',
            'vnp_Command': 'pay',
            'vnp_TmnCode': self.tmn_code,
            'vnp_Amount': str(amount * 100),  # VNPay yêu cầu nhân 100
            'vnp_CurrCode': 'VND',
            'vnp_TxnRef': txn_ref,
            'vnp_OrderInfo': clean_order_info,
            'vnp_OrderType': 'other',
            'vnp_Locale': 'vn',
            'vnp_ReturnUrl': self.return_url,
            'vnp_IpAddr': ip_addr,
            'vnp_CreateDate': create_date
        }
        
        # Tạo chữ ký từ data (KHÔNG có vnp_SecureHash)
        secure_hash = self._create_signature(vnpay_data)
        
        # Thêm secure hash VÀO URL (không thêm vào dict để tính signature)
        vnpay_data['vnp_SecureHash'] = secure_hash
        
        # Tạo URL
        query_string = urllib.parse.urlencode(vnpay_data)
        payment_url = f"{self.vnpay_url}?{query_string}"
        
        return payment_url, txn_ref
    
    def verify_return_data(self, query_params: Dict[str, str]) -> Tuple[bool, str]:
        """
        Xác thực dữ liệu trả về từ VNPay
        
        Returns:
            (is_valid, message)
        """
        # Lấy secure hash từ params
        vnp_secure_hash = query_params.get('vnp_SecureHash', '')
        
        # Loại bỏ vnp_SecureHash và vnp_SecureHashType
        data_to_verify = {
            k: v for k, v in query_params.items() 
            if k not in ['vnp_SecureHash', 'vnp_SecureHashType']
        }
        
        # Tạo chữ ký để so sánh
        calculated_hash = self._create_signature(data_to_verify)
        
        # So sánh
        if calculated_hash != vnp_secure_hash:
            return False, "Chữ ký không hợp lệ"
        
        # Kiểm tra response code
        response_code = query_params.get('vnp_ResponseCode', '')
        
        if response_code == '00':
            return True, "Giao dịch thành công"
        else:
            return False, self._get_response_message(response_code)
    
    def _get_response_message(self, code: str) -> str:
        """Lấy message từ response code"""
        messages = {
            '00': 'Giao dịch thành công',
            '07': 'Trừ tiền thành công. Giao dịch bị nghi ngờ (liên quan tới lừa đảo, giao dịch bất thường).',
            '09': 'Thẻ/Tài khoản chưa đăng ký dịch vụ InternetBanking',
            '10': 'Thẻ/Tài khoản không đúng thông tin xác thực OTP',
            '11': 'Đã hết hạn chờ thanh toán',
            '12': 'Thẻ/Tài khoản bị khóa',
            '13': 'Sai mật khẩu xác thực giao dịch (OTP)',
            '24': 'Khách hàng hủy giao dịch',
            '51': 'Tài khoản không đủ số dư',
            '65': 'Tài khoản đã vượt quá hạn mức giao dịch trong ngày',
            '72': 'Không tìm thấy website hoặc thông tin không hợp lệ',
            '75': 'Ngân hàng thanh toán đang bảo trì',
            '79': 'Giao dịch vượt quá số lần nhập sai mật khẩu',
            '99': 'Lỗi không xác định'
        }
        return messages.get(code, f'Lỗi không xác định (Code: {code})')


# Singleton instance
vnpay_service = VNPayService()