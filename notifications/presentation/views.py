from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import TokenAuthentication
from django.shortcuts import get_object_or_404

from notifications.models import Notification, NotificationPreference


class MyNotificationsApi(APIView):
    """Danh sách thông báo của tôi"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Lấy danh sách thông báo"""
        filter_type = request.query_params.get('filter', 'all')
        
        notifications = Notification.objects.filter(user=request.user)
        
        if filter_type == 'unread':
            notifications = notifications.filter(is_read=False)
        elif filter_type == 'read':
            notifications = notifications.filter(is_read=True)
        
        # Phân trang
        page = int(request.query_params.get('page', 1))
        per_page = 20
        start = (page - 1) * per_page
        end = start + per_page
        
        total = notifications.count()
        notifications_page = notifications[start:end]
        
        data = [{
            'id': n.id,
            'type': n.type,
            'type_display': n.get_type_display(),
            'title': n.title,
            'message': n.message,
            'link': n.link,
            'data': n.data,
            'is_read': n.is_read,
            'created_at': n.created_at,
            'read_at': n.read_at
        } for n in notifications_page]
        
        # Đếm số thông báo chưa đọc
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        return Response({
            'notifications': data,
            'unread_count': unread_count,
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
        })


class MarkNotificationReadApi(APIView):
    """Đánh dấu thông báo đã đọc"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, notification_id):
        """Đánh dấu một thông báo đã đọc"""
        notification = get_object_or_404(
            Notification,
            id=notification_id,
            user=request.user
        )
        
        notification.mark_as_read()
        
        return Response({
            'detail': 'Đã đánh dấu thông báo đã đọc',
            'notification_id': notification.id
        })


class MarkAllReadApi(APIView):
    """Đánh dấu tất cả thông báo đã đọc"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Đánh dấu tất cả thông báo đã đọc"""
        from django.utils import timezone
        
        updated = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({
            'detail': f'Đã đánh dấu {updated} thông báo đã đọc'
        })


class DeleteNotificationApi(APIView):
    """Xóa thông báo"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, notification_id):
        """Xóa một thông báo"""
        notification = get_object_or_404(
            Notification,
            id=notification_id,
            user=request.user
        )
        
        notification.delete()
        
        return Response({
            'detail': 'Đã xóa thông báo'
        })


class ClearAllNotificationsApi(APIView):
    """Xóa tất cả thông báo"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Xóa tất cả thông báo đã đọc"""
        deleted = Notification.objects.filter(
            user=request.user,
            is_read=True
        ).delete()[0]
        
        return Response({
            'detail': f'Đã xóa {deleted} thông báo'
        })


class NotificationPreferencesApi(APIView):
    """Cài đặt thông báo"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Xem cài đặt thông báo"""
        pref, _ = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        
        return Response({
            'email_notifications': {
                'order_updates': pref.email_order_updates,
                'promotions': pref.email_promotions,
                'flash_sales': pref.email_flash_sales
            },
            'app_notifications': {
                'order_updates': pref.app_order_updates,
                'promotions': pref.app_promotions,
                'flash_sales': pref.app_flash_sales
            }
        })
    
    def put(self, request):
        """Cập nhật cài đặt thông báo"""
        pref, _ = NotificationPreference.objects.get_or_create(
            user=request.user
        )
        
        # Email preferences
        email = request.data.get('email_notifications', {})
        if 'order_updates' in email:
            pref.email_order_updates = email['order_updates']
        if 'promotions' in email:
            pref.email_promotions = email['promotions']
        if 'flash_sales' in email:
            pref.email_flash_sales = email['flash_sales']
        
        # App preferences
        app = request.data.get('app_notifications', {})
        if 'order_updates' in app:
            pref.app_order_updates = app['order_updates']
        if 'promotions' in app:
            pref.app_promotions = app['promotions']
        if 'flash_sales' in app:
            pref.app_flash_sales = app['flash_sales']
        
        pref.save()
        
        return Response({
            'detail': 'Đã cập nhật cài đặt thông báo',
            'preferences': {
                'email_notifications': {
                    'order_updates': pref.email_order_updates,
                    'promotions': pref.email_promotions,
                    'flash_sales': pref.email_flash_sales
                },
                'app_notifications': {
                    'order_updates': pref.app_order_updates,
                    'promotions': pref.app_promotions,
                    'flash_sales': pref.app_flash_sales
                }
            }
        })


class UnreadCountApi(APIView):
    """Số lượng thông báo chưa đọc"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Lấy số thông báo chưa đọc"""
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        return Response({
            'unread_count': unread_count
        })