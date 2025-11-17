from rest_framework import serializers
class ProductSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()
    description = serializers.CharField(allow_blank=True, required=False)
    price_vnd = serializers.IntegerField(source='price.amount')
    sku = serializers.CharField(source='sku.code')
