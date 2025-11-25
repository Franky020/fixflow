from django.shortcuts import render
from rest_framework import viewsets
from .models import Company
from .serializers import CompanySerializer
from django.db.models import Count
from rest_framework.response import Response
from rest_framework.decorators import action


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """
        Calcula y retorna un conteo de compañías (excluyendo 'fixflow_internal'), 
        detallando el estado (activo/inactivo) y el desglose de planes para las activas.
        
        Endpoint: /api/companies/stats/
        """
        
        # 1. Definir el conjunto de datos base (excluyendo 'fixflow_internal')
        excluded_plan = 'fixflow_internal'
        
        # Queryset base: Todas las compañías menos la interna
        companies = self.queryset.exclude(plan_type=excluded_plan)

        # Conteo Total
        total_count = companies.count()

        # Conteo de Activas e Inactivas
        active_count = companies.filter(status='active').count()
        inactive_count = companies.filter(status='inactive').count()

        # 2. Desglose de planes para las compañías activas
        
        # Obtener el Queryset de solo compañías activas
        active_companies = companies.filter(status='active')
        
        # Agrupar y contar por tipo de plan (solo para las activas)
        plan_breakdown_qs = active_companies.values('plan_type').annotate(count=Count('plan_type'))
        
        # Formatear el resultado del desglose de planes a un diccionario más limpio
        plan_breakdown = {
            item['plan_type']: item['count']
            for item in plan_breakdown_qs
        }
        
        # Rellenar con los planes esperados si no existen en la BD (conteo 0)
        expected_plans = ['basic', 'premium', 'professional']
        for plan in expected_plans:
            if plan not in plan_breakdown:
                plan_breakdown[plan] = 0

        # 3. Construir la respuesta final
        response_data = {
            'total_companies': total_count,
            'status_summary': {
                'active': active_count,
                'inactive': inactive_count,
            },
            'active_plan_breakdown': plan_breakdown
        }

        # Retornar la respuesta usando Response de DRF (que maneja el formato JSON)
        return Response(response_data)