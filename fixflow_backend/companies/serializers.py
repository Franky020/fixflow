from rest_framework import serializers
from .models import Company  # Ajusta si tu modelo se llama distinto

class CompanySerializer(serializers.ModelSerializer):
    logo = serializers.ImageField(required=False)
    class Meta:
        model = Company
        fields = '__all__'  # Incluye todos los campos del modelo