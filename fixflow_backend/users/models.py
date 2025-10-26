from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.db import models
from companies.models import Company

class User(AbstractUser, PermissionsMixin):
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
    email = models.EmailField(max_length=254, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    user_type = models.CharField(max_length=15, choices=USER_TYPE_CHOICES, default='normal_user')
    age = models.IntegerField(blank=True, null=True)
    rfc = models.CharField(max_length=13, blank=True, null=True)
    photo = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']


    # Sobrescribiendo los campos ManyToMany para evitar colisiones
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',  # <- cambiar el related_name
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions_set',  # <- cambiar el related_name
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions'
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
