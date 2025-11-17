from django.core.management.base import BaseCommand
from catalog.infrastructure.models import ProductModel, Category
class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        cat,_ = Category.objects.get_or_create(name='Rau củ', slug='rau-cu')
        ProductModel.objects.get_or_create(
            slug='bi-do-huu-co',
            defaults=dict(name='Bí đỏ hữu cơ', description='Ngọt tự nhiên', price_vnd=35000, sku='BIDO-OC-500G', category=cat)
        )
        self.stdout.write(self.style.SUCCESS('Seeded catalog'))
