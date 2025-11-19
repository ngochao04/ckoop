from django.urls import path
from .views import (
    MyNotificationsApi, MarkNotificationReadApi, MarkAllReadApi,
    DeleteNotificationApi, ClearAllNotificationsApi,
    NotificationPreferencesApi, UnreadCountApi
)

urlpatterns = [
    # Notifications
    path('', MyNotificationsApi.as_view(), name='my_notifications'),
    path('unread-count/', UnreadCountApi.as_view(), name='unread_count'),
    path('<int:notification_id>/read/', MarkNotificationReadApi.as_view(), name='mark_read'),
    path('mark-all-read/', MarkAllReadApi.as_view(), name='mark_all_read'),
    path('<int:notification_id>/delete/', DeleteNotificationApi.as_view(), name='delete_notification'),
    path('clear-all/', ClearAllNotificationsApi.as_view(), name='clear_all'),
    
    # Preferences
    path('preferences/', NotificationPreferencesApi.as_view(), name='notification_preferences'),
]