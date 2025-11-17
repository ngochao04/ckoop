from django.contrib import admin
from .infrastructure.models import User
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username','email','is_farmer','is_staff','is_superuser')
    search_fields = ('username','email')
