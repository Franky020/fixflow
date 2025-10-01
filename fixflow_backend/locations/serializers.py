from rest_framework import serializers
from .models import Location  # Ajusta si tu modelo se llama distinto

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'  # Incluye todos los campos del modelo