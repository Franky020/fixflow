from rest_framework import serializers
from .models import User  # Ajusta si tu modelo se llama distinto

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'  # Incluye todos los campos del modelo