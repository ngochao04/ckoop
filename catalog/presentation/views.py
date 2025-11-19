from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import TokenAuthentication
from django.shortcuts import get_object_or_404

from catalog.application.services import ProductService, CreateProductInput
from catalog.infrastructure.repositories import ProductRepository
from catalog.infrastructure.models import ProductModel, Category
from .serializers import ProductSerializer


class IsAdminUser(permissions.BasePermission):
    """Chỉ admin mới có quyền"""
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class ProductListCreateApi(APIView):
    """Danh sách và tạo sản phẩm"""
    service = ProductService(ProductRepository())
    
    def get(self, request):
        # Lọc theo category nếu có
        category_id = request.query_params.get('category')
        search = request.query_params.get('search', '')
        
        queryset = ProductModel.objects.filter(is_active=True)
        
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        products = []
        for m in queryset.order_by('-id'):
            products.append({
                'id': m.id,
                'name': m.name,
                'slug': m.slug,
                'description': m.description,
                'price_vnd': m.price_vnd,
                'sku': m.sku,
                'category': {
                    'id': m.category.id,
                    'name': m.category.name
                } if m.category else None,
                'is_active': m.is_active,
                'thumbnail': m.thumbnail.url if m.thumbnail else None,
                'created_at': m.created_at
            })
        
        return Response({'products': products, 'count': len(products)})
    
    def post(self, request):
        s = ProductSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        inp = CreateProductInput(
            name=s.validated_data['name'],
            description=s.validated_data.get('description', ''),
            price_vnd=s.validated_data['price']['amount'],
            sku=s.validated_data['sku']['code']
        )
        created = self.service.create_product(inp)
        return Response(ProductSerializer(created).data, status=status.HTTP_201_CREATED)


class ProductDetailApi(APIView):
    """Chi tiết, cập nhật và xóa sản phẩm"""
    
    def get(self, request, product_id):
        """Xem chi tiết sản phẩm"""
        product = get_object_or_404(ProductModel, id=product_id)
        
        return Response({
            'id': product.id,
            'name': product.name,
            'slug': product.slug,
            'description': product.description,
            'price_vnd': product.price_vnd,
            'sku': product.sku,
            'category': {
                'id': product.category.id,
                'name': product.category.name
            } if product.category else None,
            'is_active': product.is_active,
            'thumbnail': product.thumbnail.url if product.thumbnail else None,
            'created_at': product.created_at,
            'updated_at': product.updated_at
        })
    
    def put(self, request, product_id):
        """Cập nhật sản phẩm (chỉ admin)"""
        if not request.user.is_staff:
            return Response({
                'detail': 'Bạn không có quyền thực hiện thao tác này'
            }, status=status.HTTP_403_FORBIDDEN)
        
        product = get_object_or_404(ProductModel, id=product_id)
        
        # Cập nhật các trường
        if 'name' in request.data:
            product.name = request.data['name']
        if 'description' in request.data:
            product.description = request.data['description']
        if 'price_vnd' in request.data:
            product.price_vnd = int(request.data['price_vnd'])
        if 'category_id' in request.data:
            category_id = request.data['category_id']
            if category_id:
                product.category_id = category_id
            else:
                product.category = None
        if 'is_active' in request.data:
            product.is_active = request.data['is_active']
        
        product.save()
        
        return Response({
            'detail': 'Cập nhật sản phẩm thành công',
            'product': {
                'id': product.id,
                'name': product.name,
                'price_vnd': product.price_vnd,
                'is_active': product.is_active
            }
        })
    
    def delete(self, request, product_id):
        """Xóa mềm sản phẩm (chỉ admin)"""
        if not request.user.is_staff:
            return Response({
                'detail': 'Bạn không có quyền thực hiện thao tác này'
            }, status=status.HTTP_403_FORBIDDEN)
        
        product = get_object_or_404(ProductModel, id=product_id)
        product.is_active = False
        product.save()
        
        return Response({
            'detail': 'Đã xóa sản phẩm thành công'
        })


class CategoryListCreateApi(APIView):
    """Quản lý danh mục sản phẩm"""
    
    def get(self, request):
        """Danh sách danh mục"""
        categories = Category.objects.all().order_by('name')
        
        data = [{
            'id': cat.id,
            'name': cat.name,
            'slug': cat.slug,
            'parent': {
                'id': cat.parent.id,
                'name': cat.parent.name
            } if cat.parent else None,
            'products_count': cat.productmodel_set.filter(is_active=True).count()
        } for cat in categories]
        
        return Response({'categories': data})
    
    def post(self, request):
        """Tạo danh mục mới (chỉ admin)"""
        if not request.user.is_staff:
            return Response({
                'detail': 'Bạn không có quyền thực hiện thao tác này'
            }, status=status.HTTP_403_FORBIDDEN)
        
        name = request.data.get('name')
        slug = request.data.get('slug')
        parent_id = request.data.get('parent_id')
        
        if not name or not slug:
            return Response({
                'detail': 'Name và slug là bắt buộc'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if Category.objects.filter(slug=slug).exists():
            return Response({
                'detail': 'Slug đã tồn tại'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        category = Category.objects.create(
            name=name,
            slug=slug,
            parent_id=parent_id if parent_id else None
        )
        
        return Response({
            'detail': 'Tạo danh mục thành công',
            'category': {
                'id': category.id,
                'name': category.name,
                'slug': category.slug
            }
        }, status=status.HTTP_201_CREATED)


class CategoryDetailApi(APIView):
    """Chi tiết và cập nhật danh mục"""
    
    def get(self, request, category_id):
        """Chi tiết danh mục"""
        category = get_object_or_404(Category, id=category_id)
        
        products = category.productmodel_set.filter(is_active=True)[:10]
        
        return Response({
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
            'parent': {
                'id': category.parent.id,
                'name': category.parent.name
            } if category.parent else None,
            'products_count': category.productmodel_set.filter(is_active=True).count(),
            'recent_products': [{
                'id': p.id,
                'name': p.name,
                'price_vnd': p.price_vnd
            } for p in products]
        })
    
    def put(self, request, category_id):
        """Cập nhật danh mục (chỉ admin)"""
        if not request.user.is_staff:
            return Response({
                'detail': 'Bạn không có quyền thực hiện thao tác này'
            }, status=status.HTTP_403_FORBIDDEN)
        
        category = get_object_or_404(Category, id=category_id)
        
        if 'name' in request.data:
            category.name = request.data['name']
        if 'slug' in request.data:
            new_slug = request.data['slug']
            if new_slug != category.slug and Category.objects.filter(slug=new_slug).exists():
                return Response({
                    'detail': 'Slug đã tồn tại'
                }, status=status.HTTP_400_BAD_REQUEST)
            category.slug = new_slug
        if 'parent_id' in request.data:
            category.parent_id = request.data['parent_id']
        
        category.save()
        
        return Response({
            'detail': 'Cập nhật danh mục thành công',
            'category': {
                'id': category.id,
                'name': category.name,
                'slug': category.slug
            }
        })
    
    def delete(self, request, category_id):
        """Xóa danh mục (chỉ admin)"""
        if not request.user.is_staff:
            return Response({
                'detail': 'Bạn không có quyền thực hiện thao tác này'
            }, status=status.HTTP_403_FORBIDDEN)
        
        category = get_object_or_404(Category, id=category_id)
        
        # Kiểm tra có sản phẩm không
        if category.productmodel_set.exists():
            return Response({
                'detail': 'Không thể xóa danh mục có sản phẩm. Vui lòng chuyển sản phẩm sang danh mục khác trước.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        category.delete()
        
        return Response({
            'detail': 'Đã xóa danh mục thành công'
        })


class FeaturedProductsApi(APIView):
    """Sản phẩm nổi bật"""
    
    def get(self, request):
        """Lấy 8 sản phẩm mới nhất"""
        products = ProductModel.objects.filter(is_active=True).order_by('-created_at')[:8]
        
        data = [{
            'id': p.id,
            'name': p.name,
            'slug': p.slug,
            'price_vnd': p.price_vnd,
            'thumbnail': p.thumbnail.url if p.thumbnail else None,
            'category': p.category.name if p.category else None
        } for p in products]
        
        return Response({'products': data})


class SearchSuggestionsApi(APIView):
    """Gợi ý tìm kiếm"""
    
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        
        if not query or len(query) < 2:
            return Response({'suggestions': []})
        
        products = ProductModel.objects.filter(
            name__icontains=query,
            is_active=True
        )[:5]
        
        suggestions = [{
            'id': p.id,
            'name': p.name,
            'price_vnd': p.price_vnd
        } for p in products]
        
        return Response({'suggestions': suggestions})