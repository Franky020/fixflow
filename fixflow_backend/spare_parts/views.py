from django.shortcuts import render
from rest_framework import viewsets
from .models import SparePart
from .serializers import SparePartSerializer

class SparePartViewSet(viewsets.ModelViewSet):
    queryset = SparePart.objects.all()
    

    def get_queryset(self):
        user = self.request.user

        # Super Admin ve todos
        if user.user_type == "super_admin":
            return User.objects.all()
        
         # 2. Admin: Ve todos los reportes de su propia compañía
        if user.user_type == "admin":
            # Filtra los reportes a través de la relación 'ticket__company'
            return User.objects.filter(company=user.company)

        if user.user_type == "normal_user":
            # Filtra los reportes a través de la relación 'ticket__user'
            return User.objects.filter(id=user.id)
            
        # Caso por defecto
        return user.objects.none()
    
    serializer_class = SparePartSerializer