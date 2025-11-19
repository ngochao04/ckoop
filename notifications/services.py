from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Notification, EmailLog, NotificationPreference


class NotificationService:
    """Service gửi thông báo"""
    
    @staticmethod
    def create_notification(user, notification_type, title, message, link='', data=None):
        """Tạo thông báo in-app"""
        notification = Notification.objects.create(
            user=user,
            type=notification_type,
            title=title,
            message=message,
            link=link,
            data=data or {}
        )
        return notification
    
    @staticmethod
    def send_email(to_email, subject, body, user=None):
        """Gửi email"""
        email_log = EmailLog.objects.create(
            to_email=to_email,
            subject=subject,
            body=body,
            user=user,
            status=EmailLog.Status.PENDING
        )
        
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                fail_silently=False
            )
            
            email_log.status = EmailLog.Status.SENT
            email_log.sent_at = timezone.now()
            email_log.save()
            
            return True, "Email sent successfully"
        
        except Exception as e:
            email_log.status = EmailLog.Status.FAILED
            email_log.error_message = str(e)
            email_log.save()
            
            return False, str(e)
    
    @staticmethod
    def notify_order_status_change(order, new_status):
        """Thông báo thay đổi trạng thái đơn hàng"""
        user = order.buyer
        
        # Check preferences
        pref, _ = NotificationPreference.objects.get_or_create(user=user)
        
        status_messages = {
            'paid': {
                'type': Notification.Type.ORDER_CONFIRMED,
                'title': 'Đơn hàng đã được xác nhận',
                'message': f'Đơn hàng #{order.id} đã được xác nhận và đang được chuẩn bị.'
            },
            'ship': {
                'type': Notification.Type.ORDER_SHIPPED,
                'title': 'Đơn hàng đang được giao',
                'message': f'Đơn hàng #{order.id} đang trên đường giao đến bạn.'
            },
            'done': {
                'type': Notification.Type.ORDER_DELIVERED,
                'title': 'Đơn hàng đã giao thành công',
                'message': f'Đơn hàng #{order.id} đã được giao thành công. Cảm ơn bạn đã mua hàng!'
            },
            'cancel': {
                'type': Notification.Type.ORDER_CANCELLED,
                'title': 'Đơn hàng đã bị hủy',
                'message': f'Đơn hàng #{order.id} đã bị hủy.'
            }
        }
        
        if new_status in status_messages:
            msg_data = status_messages[new_status]
            
            # In-app notification
            if pref.app_order_updates:
                NotificationService.create_notification(
                    user=user,
                    notification_type=msg_data['type'],
                    title=msg_data['title'],
                    message=msg_data['message'],
                    link=f'/orders/{order.id}/',
                    data={'order_id': order.id, 'status': new_status}
                )
            
            # Email notification
            if pref.email_order_updates and user.email:
                NotificationService.send_email(
                    to_email=user.email,
                    subject=msg_data['title'],
                    body=msg_data['message'],
                    user=user
                )
    
    @staticmethod
    def notify_payment_success(payment):
        """Thông báo thanh toán thành công"""
        user = payment.order.buyer
        pref, _ = NotificationPreference.objects.get_or_create(user=user)
        
        if pref.app_order_updates:
            NotificationService.create_notification(
                user=user,
                notification_type=Notification.Type.PAYMENT_SUCCESS,
                title='Thanh toán thành công',
                message=f'Thanh toán cho đơn hàng #{payment.order.id} đã được xác nhận.',
                link=f'/orders/{payment.order.id}/',
                data={'order_id': payment.order.id, 'payment_id': payment.id}
            )
    
    @staticmethod
    def notify_low_stock(product):
        """Thông báo sản phẩm sắp hết hàng (cho admin)"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Gửi cho tất cả admin
        admins = User.objects.filter(is_staff=True)
        
        for admin in admins:
            NotificationService.create_notification(
                user=admin,
                notification_type=Notification.Type.LOW_STOCK,
                title=f'Cảnh báo: {product.name} sắp hết hàng',
                message=f'Sản phẩm {product.name} còn {product.stock_quantity} {product.unit} trong kho.',
                link=f'/admin/catalog/productmodel/{product.id}/change/',
                data={'product_id': product.id, 'stock_quantity': product.stock_quantity}
            )
    
    @staticmethod
    def notify_flash_sale_start(flash_sale):
        """Thông báo Flash Sale bắt đầu"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Gửi cho tất cả user có bật thông báo
        users = User.objects.filter(is_active=True)
        
        for user in users:
            pref, _ = NotificationPreference.objects.get_or_create(user=user)
            
            if pref.app_flash_sales:
                NotificationService.create_notification(
                    user=user,
                    notification_type=Notification.Type.FLASH_SALE,
                    title=f'🔥 Flash Sale: {flash_sale.name}',
                    message=f'Giảm giá {flash_sale.discount_percentage}% cho hàng trăm sản phẩm!',
                    link=f'/flash-sales/{flash_sale.id}/',
                    data={'flash_sale_id': flash_sale.id}
                )
            
            if pref.email_flash_sales and user.email:
                NotificationService.send_email(
                    to_email=user.email,
                    subject=f'🔥 Flash Sale: {flash_sale.name}',
                    body=f'Giảm giá {flash_sale.discount_percentage}% đang diễn ra! Truy cập ngay để mua sắm.',
                    user=user
                )
    
    @staticmethod
    def notify_new_voucher(voucher):
        """Thông báo voucher mới"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Chỉ gửi cho voucher công khai
        if not voucher.is_public:
            return
        
        users = User.objects.filter(is_active=True, is_customer=True)
        
        for user in users:
            pref, _ = NotificationPreference.objects.get_or_create(user=user)
            
            if pref.app_promotions:
                discount_text = f"{voucher.discount_value}%" if voucher.discount_type == 'percentage' else f"{voucher.discount_value:,}₫"
                
                NotificationService.create_notification(
                    user=user,
                    notification_type=Notification.Type.PROMOTION,
                    title=f'🎁 Voucher mới: {voucher.name}',
                    message=f'Nhập mã "{voucher.code}" để giảm {discount_text}',
                    link='/vouchers/',
                    data={'voucher_id': voucher.id, 'code': voucher.code}
                )