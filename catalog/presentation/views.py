from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from catalog.application.services import ProductService, CreateProductInput
from catalog.infrastructure.repositories import ProductRepository
from .serializers import ProductSerializer
class ProductListCreateApi(APIView):
    service = ProductService(ProductRepository())
    def get(self, request):
        products = list(self.service.list_products())
        data = ProductSerializer(products, many=True).data
        return Response(data)
    def post(self, request):
        s = ProductSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        inp = CreateProductInput(
            name=s.validated_data['name'],
            description=s.validated_data.get('description',''),
            price_vnd=s.validated_data['price']['amount'],
            sku=s.validated_data['sku']['code']
        )
        created = self.service.create_product(inp)
        return Response(ProductSerializer(created).data, status=status.HTTP_201_CREATED)
