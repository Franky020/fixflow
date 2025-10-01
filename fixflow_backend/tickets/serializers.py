from rest_framework import serializers
from .models import Ticket  # Ajusta si tu modelo se llama distinto

class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = '__all__'  # Incluye todos los campos del modelo