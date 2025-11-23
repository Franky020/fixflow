from rest_framework import serializers
from .models import CustomerSatisfaction

class CustomerSatisfactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerSatisfaction
        fields = ['id', 'ticket', 'rating', 'message', 'created_at']
        read_only_fields = ['created_at']