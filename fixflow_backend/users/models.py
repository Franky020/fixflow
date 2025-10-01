from django.db import models
from companies.models import Company

class User(models.Model):
    USER_TYPE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('admin', 'Admin'),
        ('normal_user', 'Normal User')
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='users')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    user_type = models.CharField(max_length=15, choices=USER_TYPE_CHOICES, default='normal_user')
    age = models.IntegerField(blank=True, null=True)
    rfc = models.CharField(max_length=13, blank=True, null=True)
    photo = models.CharField(max_length=255, blank=True, null=True)
    password_hash = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"