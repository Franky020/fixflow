from django.db import models
from users.models import Company, User


class Ticket(models.Model):
    CATEGORY_CHOICES = [
        ('corrective', 'Corrective'),
        ('preventive', 'Preventive'),
        ('predictive', 'Predictive'),
        ('none', 'None')
    ]
    PRIORITY_CHOICES = [
        ('none', 'None'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ]
    STATUS_CHOICES = [
        ('abierto', 'Abierto'),
        ('en_curso', 'En curso'),
        ('cerrado', 'Cerrado'),
        ('en_espera', 'En espera'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='tickets')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tickets')
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, default='none')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='none')
    # ✅ Solución: referencia por string
    location = models.ForeignKey('locations.Location', on_delete=models.SET_NULL, blank=True, null=True, related_name='tickets')
    equipment = models.CharField(max_length=150, blank=True, null=True)
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    duration = models.DurationField(blank=True, null=True)
    report = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='en_espera')

    def __str__(self):
        return self.title
