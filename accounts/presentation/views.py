from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, get_user_model
from rest_framework.authentication import TokenAuthentication

User = get_user_model()

class RegisterApi(APIView):
    """Đăng ký tài khoản mới"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        phone = request.data.get('phone', '')
        is_farmer = request.data.get('is_farmer', False)
        
        if not username or not password:
            return Response({
                'detail': 'Username và password là bắt buộc'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(username=username).exists():
            return Response({
                'detail': 'Username đã tồn tại'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            phone=phone,
            is_farmer=is_farmer
        )
        
        token, _ = Token.objects.get_or_create(user=user)
        
        return Response({
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'is_farmer': user.is_farmer,
            'token': token.key
        }, status=status.HTTP_201_CREATED)


class LoginApi(APIView):
    """Đăng nhập"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        
        if not user:
            return Response({
                'detail': 'Thông tin đăng nhập không đúng'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        token, _ = Token.objects.get_or_create(user=user)
        
        return Response({
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'is_farmer': user.is_farmer,
            'token': token.key
        })


class LogoutApi(APIView):
    """Đăng xuất"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        request.user.auth_token.delete()
        return Response({'detail': 'Đăng xuất thành công'})


class ProfileApi(APIView):
    """Xem và cập nhật profile"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        return Response({
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'phone': user.phone,
            'is_farmer': user.is_farmer,
            'is_customer': user.is_customer,
            'date_joined': user.date_joined
        })
    
    def put(self, request):
        user = request.user
        
        if 'email' in request.data:
            user.email = request.data['email']
        if 'phone' in request.data:
            user.phone = request.data['phone']
        
        user.save()
        
        return Response({
            'detail': 'Cập nhật thành công',
            'user': {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': user.phone
            }
        })