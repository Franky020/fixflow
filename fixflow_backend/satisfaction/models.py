# satisfaction/models.py
from django.db import models
from tickets.models import Ticket
# Importamos el módulo Decimal para precisión
from decimal import Decimal 

# Definimos las opciones de calificación como constantes de Decimal
RATING_CHOICES = [
    (Decimal('1.0'), '1.0'),
    (Decimal('1.5'), '1.5'),
    (Decimal('2.0'), '2.0'),
    (Decimal('2.5'), '2.5'),
    (Decimal('3.0'), '3.0'),
    (Decimal('3.5'), '3.5'),
    (Decimal('4.0'), '4.0'),
    (Decimal('4.5'), '4.5'),
    (Decimal('5.0'), '5.0'),
]

class CustomerSatisfaction(models.Model):
    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=1, 
        # Usamos las opciones predefinidas con Decimal
        choices=RATING_CHOICES, 
        help_text="Calificación del cliente (1.0 a 5.0)"
    )
    
    # ... (el resto de tu modelo sigue igual) ...
    message = models.TextField(blank=True, null=True)
    
    ticket = models.OneToOneField(
        Ticket, 
        on_delete=models.CASCADE, 
        related_name='satisfaction'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Satisfacción del Cliente"
        verbose_name_plural = "Satisfacciones del Cliente"

    def __str__(self):
        return f"Calificación {self.rating} para Ticket #{self.ticket.id}"

