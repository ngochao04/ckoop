from django.contrib.auth.models import AbstractUser
from django.db import models
class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True)
    is_farmer = models.BooleanField(default=False)
    is_customer = models.BooleanField(default=True)
