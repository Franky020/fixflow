from django.shortcuts import render
from rest_framework import viewsets
from .models import Location
from .serializers import LocationSerializer
from locations.permissions import CompanyAccessPermission

class LocationViewSet(viewsets.ModelViewSet):
    permission_classes = [CompanyAccessPermission]
    serializer_class = LocationSerializer

    def get_queryset(self):
        user = self.request.user

        # Super Admin ve todos
        if user.user_type == "super_admin":
            return Location.objects.all()
        
         # 2. Admin: Ve todos los reportes de su propia compañía
        if user.user_type == "admin":
            # Filtra los reportes a través de la relación 'ticket__company'
            return Location.objects.filter(company=user.company)

        if user.user_type == "normal_user":
            # Filtra los reportes a través de la relación 'ticket__user'
            return Location.objects.filter(user=user)
            
        # Caso por defecto
        return Location.objects.none()
