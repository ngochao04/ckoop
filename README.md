# CleanAgri (Django + OOP + PostgreSQL only)
## Chạy nhanh
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# tạo user/db trong postgres trước (xem POSTGRES.md)
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_catalog
python manage.py runserver
```
## API
- GET  /api/catalog/products/
- POST /api/catalog/products/  {"name":"Táo hữu cơ","description":"","price_vnd":42000,"sku":"TAO-OC-1"}
- POST /api/cart/add/  {"product_id":1,"qty":2}
- GET  /api/cart/me/
- POST /api/orders/checkout/
