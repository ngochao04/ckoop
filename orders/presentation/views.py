from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import get_user_model
from orders.application.services import OrderService, CheckoutInput
class CheckoutApi(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        user = get_user_model().objects.first()
        if not user:
            return Response({'detail':'Chưa có user. Tạo superuser trước.'}, status=400)
        order_id = OrderService().checkout(CheckoutInput(user_id=user.id))
        return Response({'order_id': order_id}, status=status.HTTP_201_CREATED)
