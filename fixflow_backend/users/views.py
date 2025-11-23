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


# Configuración de log
logger = logging.getLogger(__name__)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [CompanyAccessPermission]
    serializer_class = UserSerializer

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
