from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authentication import TokenAuthentication
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Count, Q
from django.db import models

from catalog.infrastructure.models import ProductModel, ProductReview, ReviewHelpful
from orders.infrastructure.models import OrderModel, OrderLineModel


class ProductReviewListApi(APIView):
    """Xem danh sách đánh giá của sản phẩm"""
    
    def get(self, request, product_id):
        """Lấy tất cả đánh giá của sản phẩm"""
        product = get_object_or_404(ProductModel, id=product_id)
        
        # Lọc theo rating
        rating_filter = request.query_params.get('rating')
        
        reviews = ProductReview.objects.filter(product=product).select_related('user')
        
        if rating_filter:
            reviews = reviews.filter(rating=int(rating_filter))
        
        # Sắp xếp
        sort_by = request.query_params.get('sort', 'newest')
        if sort_by == 'oldest':
            reviews = reviews.order_by('created_at')
        elif sort_by == 'helpful':
            reviews = reviews.order_by('-helpful_count', '-created_at')
        else:  # newest
            reviews = reviews.order_by('-created_at')
        
        # Phân trang
        page = int(request.query_params.get('page', 1))
        per_page = 10
        start = (page - 1) * per_page
        end = start + per_page
        
        total = reviews.count()
        reviews_page = reviews[start:end]
        
        # Thống kê rating
        rating_stats = ProductReview.objects.filter(product=product).aggregate(
            avg_rating=Avg('rating'),
            total_reviews=Count('id'),
            rating_5=Count('id', filter=models.Q(rating=5)),
            rating_4=Count('id', filter=models.Q(rating=4)),
            rating_3=Count('id', filter=models.Q(rating=3)),
            rating_2=Count('id', filter=models.Q(rating=2)),
            rating_1=Count('id', filter=models.Q(rating=1)),
        )
        
        data = [{
            'id': r.id,
            'user': {
                'username': r.user.username,
                'is_verified_purchase': r.is_verified_purchase
            },
            'rating': r.rating,
            'title': r.title,
            'content': r.content,
            'images': r.images,
            'helpful_count': r.helpful_count,
            'created_at': r.created_at,
            'updated_at': r.updated_at
        } for r in reviews_page]
        
        return Response({
            'reviews': data,
            'rating_stats': {
                'avg_rating': round(rating_stats['avg_rating'] or 0, 1),
                'total_reviews': rating_stats['total_reviews'],
                'rating_distribution': {
                    '5': rating_stats['rating_5'],
                    '4': rating_stats['rating_4'],
                    '3': rating_stats['rating_3'],
                    '2': rating_stats['rating_2'],
                    '1': rating_stats['rating_1'],
                }
            },
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
        })


class ProductReviewCreateApi(APIView):
    """Tạo đánh giá sản phẩm"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, product_id):
        """Viết đánh giá cho sản phẩm"""
        product = get_object_or_404(ProductModel, id=product_id)
        
        # ✅ Lấy dữ liệu từ request
        rating = request.data.get('rating')
        title = request.data.get('title', '')
        content = request.data.get('content', '')
        order_id = request.data.get('order_id')  # Optional
        
        # Validate
        if not rating:
            return Response({
                'detail': 'Rating là bắt buộc'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            rating = int(rating)
        except (ValueError, TypeError):
            return Response({
                'detail': 'Rating phải là số'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if rating < 1 or rating > 5:
            return Response({
                'detail': 'Rating phải từ 1-5'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not content or not content.strip():
            return Response({
                'detail': 'Nội dung đánh giá là bắt buộc'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Kiểm tra đã mua hàng chưa
        is_verified_purchase = False
        order = None
        
        if order_id:
            order = OrderModel.objects.filter(
                id=order_id,
                buyer=request.user,
                status__in=[OrderModel.Status.DONE]
            ).first()
            
            if order:
                has_product = OrderLineModel.objects.filter(
                    order=order,
                    product_name=product.name
                ).exists()
                
                if has_product:
                    is_verified_purchase = True
        
        # ✅ KIỂM TRA: Đã đánh giá chưa
        # Cho phép user đánh giá lại (xóa review cũ trước khi tạo mới)
        existing_review = ProductReview.objects.filter(
            product=product,
            user=request.user,
            order=order
        ).first()
        
        if existing_review:
            # Xóa review cũ để user có thể đánh giá lại
            existing_review.delete()
        
        # ✅ TẠO review mới
        try:
            review = ProductReview.objects.create(
                product=product,
                user=request.user,
                order=order,
                rating=rating,
                title=title,
                content=content,
                is_verified_purchase=is_verified_purchase
            )
            
            return Response({
                'detail': 'Đã tạo đánh giá thành công',
                'review': {
                    'id': review.id,
                    'rating': review.rating,
                    'title': review.title,
                    'is_verified_purchase': review.is_verified_purchase,
                    'created_at': review.created_at
                }
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            print(f'Error creating review: {str(e)}')
            return Response({
                'detail': f'Lỗi khi tạo đánh giá: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class ReviewHelpfulApi(APIView):
    """Đánh dấu review hữu ích"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, review_id):
        """Vote review hữu ích"""
        review = get_object_or_404(ProductReview, id=review_id)
        
        # Kiểm tra đã vote chưa
        helpful, created = ReviewHelpful.objects.get_or_create(
            review=review,
            user=request.user
        )
        
        if created:
            # Tăng helpful_count
            review.helpful_count += 1
            review.save()
            
            return Response({
                'detail': 'Đã đánh dấu hữu ích',
                'helpful_count': review.helpful_count
            })
        else:
            # Đã vote rồi, bỏ vote
            helpful.delete()
            review.helpful_count = max(0, review.helpful_count - 1)
            review.save()
            
            return Response({
                'detail': 'Đã bỏ đánh dấu hữu ích',
                'helpful_count': review.helpful_count
            })


class MyReviewsApi(APIView):
    """Xem các đánh giá của tôi"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Lấy tất cả đánh giá của user"""
        reviews = ProductReview.objects.filter(
            user=request.user
        ).select_related('product').order_by('-created_at')
        
        data = [{
            'id': r.id,
            'product': {
                'id': r.product.id,
                'name': r.product.name,
                'thumbnail': r.product.thumbnail.url if r.product.thumbnail else None
            },
            'rating': r.rating,
            'title': r.title,
            'content': r.content,
            'helpful_count': r.helpful_count,
            'is_verified_purchase': r.is_verified_purchase,
            'created_at': r.created_at
        } for r in reviews]
        
        return Response({
            'reviews': data,
            'count': len(data)
        })