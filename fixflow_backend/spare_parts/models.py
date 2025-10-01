from django.db import models
from companies.models import Company
from users.models import User
from tickets.models import Ticket

class SparePart(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='spare_parts')
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    serial_number = models.CharField(max_length=50, blank=True, null=True)
    min_stock = models.IntegerField(default=0)
    stock = models.IntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return self.name
    
class SparePartMovement(models.Model):
    MOVEMENT_CHOICES = [
        ('output', 'Output'),
        ('input', 'Input'),
        ('adjustment', 'Adjustment')
    ]

    spare_part = models.ForeignKey(SparePart, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_CHOICES)
    ticket = models.ForeignKey(Ticket, on_delete=models.SET_NULL, blank=True, null=True, related_name='spare_part_movements')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='spare_part_movements')
    movement_date = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True, null=True)


class TicketSparePart(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    spare_part = models.ForeignKey(SparePart, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    class Meta:
        unique_together = ('ticket', 'spare_part')
