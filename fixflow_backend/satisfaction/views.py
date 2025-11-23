from django.shortcuts import render
from rest_framework import viewsets
from .models import CustomerSatisfaction
from .serializers import CustomerSatisfactionSerializer
from rest_framework.permissions import AllowAny 

class CustomerSatisfactionViewSet(viewsets.ModelViewSet):
    queryset = CustomerSatisfaction.objects.all()
    serializer_class = CustomerSatisfactionSerializer
    # Permite a cualquiera (incluso sin login) crear una calificación 
    # si así lo requieres para un formulario público. Si solo es para usuarios logueados, usa IsAuthenticated.
    permission_classes = [AllowAny] 