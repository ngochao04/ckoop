from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import TokenAuthentication
from django.shortcuts import get_object_or_404

from accounts.infrastructure.models import ShippingAddress


class AddressListCreateApi(APIView):
    """Danh sách và tạo địa chỉ giao hàng"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Lấy danh sách địa chỉ của user"""
        addresses = ShippingAddress.objects.filter(user=request.user)
        
        data = [{
            'id': addr.id,
            'full_name': addr.full_name,
            'phone': addr.phone,
            'province': addr.province,
            'district': addr.district,
            'ward': addr.ward,
            'address_line': addr.address_line,
            'is_default': addr.is_default,
            'full_address': str(addr),
            'created_at': addr.created_at
        } for addr in addresses]
        
        return Response({
            'addresses': data,
            'count': len(data)
        })
    
    def post(self, request):
        """Tạo địa chỉ mới"""
        required_fields = ['full_name', 'phone', 'province', 'district', 'ward', 'address_line']
        
        # Validate required fields
        for field in required_fields:
            if not request.data.get(field):
                return Response({
                    'detail': f'Trường {field} là bắt buộc'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create address
        address = ShippingAddress.objects.create(
            user=request.user,
            full_name=request.data['full_name'],
            phone=request.data['phone'],
            province=request.data['province'],
            district=request.data['district'],
            ward=request.data['ward'],
            address_line=request.data['address_line'],
            is_default=request.data.get('is_default', False)
        )
        
        return Response({
            'detail': 'Tạo địa chỉ thành công',
            'address': {
                'id': address.id,
                'full_name': address.full_name,
                'phone': address.phone,
                'full_address': str(address),
                'is_default': address.is_default
            }
        }, status=status.HTTP_201_CREATED)


class AddressDetailApi(APIView):
    """Chi tiết, cập nhật và xóa địa chỉ"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, address_id):
        """Xem chi tiết địa chỉ"""
        address = get_object_or_404(
            ShippingAddress, 
            id=address_id, 
            user=request.user
        )
        
        return Response({
            'id': address.id,
            'full_name': address.full_name,
            'phone': address.phone,
            'province': address.province,
            'district': address.district,
            'ward': address.ward,
            'address_line': address.address_line,
            'is_default': address.is_default,
            'full_address': str(address),
            'created_at': address.created_at,
            'updated_at': address.updated_at
        })
    
    def put(self, request, address_id):
        """Cập nhật địa chỉ"""
        address = get_object_or_404(
            ShippingAddress, 
            id=address_id, 
            user=request.user
        )
        
        # Update fields
        updatable_fields = [
            'full_name', 'phone', 'province', 'district', 
            'ward', 'address_line', 'is_default'
        ]
        
        for field in updatable_fields:
            if field in request.data:
                setattr(address, field, request.data[field])
        
        address.save()
        
        return Response({
            'detail': 'Cập nhật địa chỉ thành công',
            'address': {
                'id': address.id,
                'full_name': address.full_name,
                'full_address': str(address),
                'is_default': address.is_default
            }
        })
    
    def delete(self, request, address_id):
        """Xóa địa chỉ"""
        address = get_object_or_404(
            ShippingAddress, 
            id=address_id, 
            user=request.user
        )
        
        # Không cho xóa địa chỉ mặc định nếu còn địa chỉ khác
        if address.is_default:
            other_addresses = ShippingAddress.objects.filter(
                user=request.user
            ).exclude(id=address_id)
            
            if other_addresses.exists():
                return Response({
                    'detail': 'Vui lòng đặt địa chỉ khác làm mặc định trước khi xóa'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        address.delete()
        
        return Response({
            'detail': 'Đã xóa địa chỉ thành công'
        })


class SetDefaultAddressApi(APIView):
    """Đặt địa chỉ mặc định"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, address_id):
        """Đặt địa chỉ làm mặc định"""
        address = get_object_or_404(
            ShippingAddress, 
            id=address_id, 
            user=request.user
        )
        
        # Bỏ mặc định của tất cả địa chỉ khác
        ShippingAddress.objects.filter(
            user=request.user
        ).update(is_default=False)
        
        # Đặt địa chỉ này làm mặc định
        address.is_default = True
        address.save()
        
        return Response({
            'detail': 'Đã đặt làm địa chỉ mặc định',
            'address': {
                'id': address.id,
                'full_address': str(address)
            }
        })


class AddressProvinceApi(APIView):
    """API lấy danh sách tỉnh/thành phố (mock data)"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """Danh sách tỉnh thành phố Việt Nam"""
        # Mock data - trong thực tế nên dùng API của bên thứ 3
        provinces = [
            'Hà Nội', 'TP. Hồ Chí Minh', 'Đà Nẵng', 'Hải Phòng', 'Cần Thơ',
            'An Giang', 'Bà Rịa - Vũng Tàu', 'Bắc Giang', 'Bắc Kạn', 'Bạc Liêu',
            'Bắc Ninh', 'Bến Tre', 'Bình Định', 'Bình Dương', 'Bình Phước',
            'Bình Thuận', 'Cà Mau', 'Cao Bằng', 'Đắk Lắk', 'Đắk Nông',
            'Điện Biên', 'Đồng Nai', 'Đồng Tháp', 'Gia Lai', 'Hà Giang',
            'Hà Nam', 'Hà Tĩnh', 'Hải Dương', 'Hậu Giang', 'Hòa Bình',
            'Hưng Yên', 'Khánh Hòa', 'Kiên Giang', 'Kon Tum', 'Lai Châu',
            'Lâm Đồng', 'Lạng Sơn', 'Lào Cai', 'Long An', 'Nam Định',
            'Nghệ An', 'Ninh Bình', 'Ninh Thuận', 'Phú Thọ', 'Phú Yên',
            'Quảng Bình', 'Quảng Nam', 'Quảng Ngãi', 'Quảng Ninh', 'Quảng Trị',
            'Sóc Trăng', 'Sơn La', 'Tây Ninh', 'Thái Bình', 'Thái Nguyên',
            'Thanh Hóa', 'Thừa Thiên Huế', 'Tiền Giang', 'Trà Vinh', 'Tuyên Quang',
            'Vĩnh Long', 'Vĩnh Phúc', 'Yên Bái'
        ]
        
        return Response({
            'provinces': sorted(provinces)
        })