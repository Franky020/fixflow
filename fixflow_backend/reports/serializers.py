from rest_framework import serializers
from .models import Report  # Ajusta si tu modelo se llama distinto

class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = '__all__'  # Incluye todos los campos del modelo