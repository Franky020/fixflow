from django.shortcuts import render
from rest_framework import viewsets
from .models import User
from .serializers import UserSerializer
from django.views.decorators.csrf import csrf_exempt
import json
from .serializers import Login
import logging
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse
from rest_framework.decorators import action 
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.hashers import check_password
from users.permissions import CompanyAccessPermission
from django.db.models import Count



# Configuración de log
logger = logging.getLogger(__name__)

class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [CompanyAccessPermission]
    serializer_class = UserSerializer

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


    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], url_path='update-photo')
    def update_photo(self, request):
        user = request.user

        if "photo" not in request.FILES:
            return Response(
                {"error": "Se requiere una imagen."},
                status=status.HTTP_400_BAD_REQUEST
            )

        photo = request.FILES["photo"]
        user.photo = photo
        user.save()

        return Response(
            {
                "message": "Foto actualizada correctamente",
                "photo_url": user.photo.url
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'], url_path='user_type_counts')
    def user_type_counts(self, request):
        """
        Calcula el conteo de usuarios por cada compañía y por tipo de usuario (user_type).
        Usa self.get_queryset() para garantizar la aplicación de permisos.
        
        Endpoint: /api/users/user_type_counts/
        """
        
        # 1. Query de Agregación
        # Se usa self.get_queryset() para obtener la lista de usuarios, aplicando la lógica de permisos.
        user_counts = self.get_queryset().values( 
            # Agrupar por ID de compañía y nombre de compañía
            'company_id', 
            'company__name',
            # Agrupar por tipo de usuario
            'user_type'
        ).annotate(
            # Contar el número de usuarios en cada grupo
            count=Count('id')
        ).order_by('company__name', 'user_type')

        # 2. Reestructurar el resultado para un formato más legible
        result = {}
        
        for item in user_counts:
            # Usar .get() para evitar errores si company_name fuera None por alguna razón
            company_name = item.get('company__name', 'Sin Compañía Asignada')
            
            # Si el usuario es un Normal User, solo se ve a sí mismo, por lo que 
            # company_name puede ser None si el campo no es obligatorio.
            # Aquí asumimos que si no hay company_id, el nombre tampoco existe.
            if not company_name and item['company_id'] is None:
                company_name = "Usuarios sin Compañía"


            user_type = item['user_type']
            count = item['count']
            
            # Usar el nombre de la compañía como clave principal
            if company_name not in result:
                # Inicializar el diccionario de tipos de usuario para la nueva compañía
                result[company_name] = {
                    'total_users': 0, 
                    'roles': {}
                }
            
            # Asignar el conteo al tipo de usuario (rol) dentro de la compañía
            result[company_name]['roles'][user_type] = count
            
            # Acumular el conteo total de usuarios para la compañía
            result[company_name]['total_users'] += count

        # 3. Retornar la respuesta
        return Response(result)
    
    @action(detail=False, methods=['post'], url_path='change_password')
    def change_password(self, request):
        user = request.user

        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if not current_password or not new_password or not confirm_password:
            return Response(
                {"error": "Completa todos los campos."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not check_password(current_password, user.password):
            return Response(
                {"error": "La contraseña actual es incorrecta."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_password != confirm_password:
            return Response(
                {"error": "Las contraseñas nuevas no coinciden."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()

        return Response(
            {"message": "Contraseña actualizada correctamente."},
            status=status.HTTP_200_OK
        )
    
class LoginView(TokenObtainPairView):
    serializer_class = Login

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")

            if refresh_token is None:
                return Response(
                    {"error": "El token de actualización es requerido."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"message": "Sesión cerrada correctamente."},
                status=status.HTTP_205_RESET_CONTENT
            )
        except Exception as e:
            return Response(
                {"error": f"Ocurrió un error al cerrar sesión: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
class RegisterDeviceTokenView(APIView):
    def post(self, request):
        user = request.user
        token = request.data.get('device_token')

        if not token:
            return Response({"error": "Device token is required"}, status=status.HTTP_400_BAD_REQUEST)

        user.device_token = token
        user.save()
        return Response({"message": "Token saved successfully"}, status=status.HTTP_200_OK)
