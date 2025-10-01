from django.db import models
from companies.models import Company

class Location(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='locations')
    name = models.CharField(max_length=150)
    address = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name
