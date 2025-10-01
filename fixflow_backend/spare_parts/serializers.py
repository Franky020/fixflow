from rest_framework import serializers
from .models import SparePart  # Ajusta si tu modelo se llama distinto

class SparePartSerializer(serializers.ModelSerializer):
    class Meta:
        model = SparePart
        fields = '__all__'  # Incluye todos los campos del modelo