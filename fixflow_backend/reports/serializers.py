from rest_framework import serializers
from .models import Report, ReportMessage  # Ajusta si tu modelo se llama distinto

class ReportMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportMessage
        fields = ['id', 'message', 'image', 'created_at']
        read_only_fields = ['created_at']  # Opcional

class ReportSerializer(serializers.ModelSerializer):
    messages = ReportMessageSerializer(many=True, read_only=True)
    class Meta:
        model = Report
        fields = '__all__'  # Incluye todos los campos del modelo

class AddReportMessageSerializer(serializers.Serializer):
    message = serializers.CharField()
    image = serializers.ImageField(required=False)