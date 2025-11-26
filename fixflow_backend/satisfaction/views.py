from django.shortcuts import render
from .models import CustomerSatisfaction
from .serializers import CustomerSatisfactionSerializer
from rest_framework.permissions import AllowAny 
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Avg, Case, When, DecimalField # Importar Avg y Case
from django.db.models.functions import Coalesce # Para manejar promedios nulos
from tickets.models import Ticket # Necesario para filtrar tickets

class CustomerSatisfactionViewSet(viewsets.ModelViewSet):
    queryset = CustomerSatisfaction.objects.all()
    serializer_class = CustomerSatisfactionSerializer
    # Permite a cualquiera (incluso sin login) crear una calificación 
    # si así lo requieres para un formulario público. Si solo es para usuarios logueados, usa IsAuthenticated.
    permission_classes = [AllowAny] 

    @action(detail=False, methods=['get'], url_path='satisfaction-stats')
    def satisfaction_stats(self, request):
        """
        Calcula la distribución de calificaciones y la calificación promedio general (CSAT).

        Endpoint sugerido: /api/satisfaction/satisfaction-stats/
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
    