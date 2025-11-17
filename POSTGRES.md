# PostgreSQL trực tiếp (không Docker)
## Tạo user & DB (psql bằng superuser)
```sql
CREATE ROLE cleanagri LOGIN PASSWORD 'cleanagri';
CREATE DATABASE cleanagri OWNER cleanagri;
GRANT ALL PRIVILEGES ON DATABASE cleanagri TO cleanagri;
```
## .env
```
DEBUG=True
SECRET_KEY=replace-this-with-a-secure-key
ALLOWED_HOSTS=127.0.0.1,localhost
DB_NAME=cleanagri
DB_USER=cleanagri
DB_PASSWORD=cleanagri
DB_HOST=localhost
DB_PORT=5432
```
## Lỗi hay gặp
- connection refused → kiểm tra service Postgres & port 5432
- password authentication failed → sai user/pass
- no pg_hba.conf entry → thêm rule md5 cho localhost và restart Postgres
