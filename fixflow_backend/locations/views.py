from django.shortcuts import render
from rest_framework import viewsets
from .models import Location
from .serializers import LocationSerializer
from locations.permissions import CompanyAccessPermission

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    permission_classes = [CompanyAccessPermission]
    serializer_class = LocationSerializer
