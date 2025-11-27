from django.shortcuts import render
from .models import CustomerSatisfaction
from .serializers import CustomerSatisfactionSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated 
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Avg, Case, When, DecimalField
from django.db.models.functions import Coalesce 
from tickets.models import Ticket 
from satisfaction.permissions import CompanyAccessPermission # Asumo que tienes esta importación

class CustomerSatisfactionViewSet(viewsets.ModelViewSet):
    # La clase ya NO tiene 'permission_classes = [CompanyAccessPermission]'
    serializer_class = CustomerSatisfactionSerializer

    def get_permissions(self):
        """
        Instancia y retorna la lista de permisos que este ViewSet requiere 
        basándose en la acción solicitada.
        """
        if self.action == 'create':
            # 💡 Acción 'create' (POST): Permite a cualquiera sin autenticación.
            permission_classes = [AllowAny]
        else:
            # 🔒 Demás acciones (list, retrieve, update, destroy, satisfaction_stats):
            # Requieren el permiso personalizado que valida la compañía/usuario.
            permission_classes = [CompanyAccessPermission] 
            
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        
        # Si el usuario no está autenticado, no tiene permiso para listar/ver
        # (esto se maneja en get_permissions, pero get_queryset debe ser robusto)
        if not user.is_authenticated:
             # Retorna un queryset vacío si no hay usuario autenticado y la acción no es 'create'
            return CustomerSatisfaction.objects.none() 

        # Super Admin ve todos
        if user.user_type == "super_admin":
            return CustomerSatisfaction.objects.all()
        
        # Admin: Ve todos los reportes de su propia compañía
        if user.user_type == "admin":
            # Filtra los reportes a través de la relación 'ticket__company'
            return CustomerSatisfaction.objects.filter(ticket__company=user.company)

        if user.user_type == "normal_user":
            # Filtra los reportes a través de la relación 'ticket__user'
            return CustomerSatisfaction.objects.filter(ticket__user=user)
            
        # Caso por defecto
        return CustomerSatisfaction.objects.none()

    @action(detail=False, methods=['get'], url_path='satisfaction-stats')
    def satisfaction_stats(self, request):
        """
        Calcula la distribución de calificaciones y la calificación promedio general (CSAT).
        
        Este método estará protegido por CompanyAccessPermission (definido en get_permissions).
        """
        
        # 1. Obtener el QuerySet de satisfacciones filtrado por permisos
        satisfaction_queryset = self.get_queryset()

        if satisfaction_queryset.model.objects is None:
             return Response(
                 {"error": "El modelo CustomerSatisfaction no está disponible o la importación falló."},
                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
             )
            
        # 2. Calcular el promedio de calificación (CSAT)
        # Usamos Coalesce para que el promedio sea 0 si no hay registros.
        average_rating = satisfaction_queryset.aggregate(
            csat=Coalesce(Avg('rating'), 0.0, output_field=DecimalField())
        )['csat']

        # 3. Calcular la distribución de calificaciones
        rating_distribution = satisfaction_queryset.values('rating').annotate(
            count=Count('rating')
        ).order_by('rating')

        # 4. Estructurar el resultado final
        
        # Convertir la lista de resultados de la distribución a un diccionario para fácil consumo
        distribution_dict = {
            float(item['rating']): item['count']
            for item in rating_distribution
        }
        
        result = {
            "overall_csat": round(float(average_rating), 2), # Redondear a 2 decimales para mostrar
            "total_reviews": satisfaction_queryset.count(),
            "rating_distribution": distribution_dict,
        }

        # 5. Retornar la respuesta
        return Response(result)