from django.shortcuts import render
from rest_framework import viewsets
from .models import Ticket
from .serializers import TicketSerializer
from django.conf import settings
import requests
from firebase_admin import messaging
from firebase_config import *
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count
from rest_framework.permissions import IsAuthenticated
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from reports.models import Report, ReportMessage
from reportlab.lib.units import inch
from tickets.permissions import CompanyAccessPermission
from django.db.models import Count


class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [CompanyAccessPermission]

    def get_queryset(self):
        user = self.request.user

        # Super Admin ve todos
        if user.user_type == "super_admin":
            return Ticket.objects.all()
        
         # 2. Admin: Ve todos los reportes de su propia compañía
        if user.user_type == "admin":
            # Filtra los reportes a través de la relación 'ticket__company'
            return Ticket.objects.filter(company=user.company)

        if user.user_type == "normal_user":
            # Filtra los reportes a través de la relación 'ticket__user'
            return Ticket.objects.filter(user=user)
            
        # Caso por defecto
        return Ticket.objects.none()
    def send_push_notification(token, title, body):
        # Crea la notificación
        notification = messaging.Notification(
            title=title,
            body=body
        )

        # Crea el mensaje
        message = messaging.Message(
            notification=notification,
            token=token
        )

        try:
            response = messaging.send(message)
            print(f"✅ Notificación enviada correctamente: {response}")
        except Exception as e:
            print(f"⚠️ Error al enviar notificación: {e}")

    @action(detail=False, methods=['get'], url_path='by_user/(?P<user_id>[^/.]+)')
    def by_user(self, request, user_id=None):
        tickets = Ticket.objects.filter(user_id=user_id)

        if not tickets.exists():
            return Response(
                {"message": "El usuario no tiene tickets asignados."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(tickets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='count_by_status')
    def count_by_status(self, request):
        user = request.user  # Usuario autenticado

        # Ajusta según cómo defines los estados en tu modelo
        estados = ["abierto", "en_curso", "cerrado", "en_espera"]

        conteo = {}

        for estado in estados:
            conteo[estado] = Ticket.objects.filter(user=user, status=estado).count()

        conteo["total"] = Ticket.objects.filter(user=user).count()

        return Response(conteo, status=status.HTTP_200_OK)
    

    # ---- CONTAR TICKETS DEL USUARIO EXCEPTO LOS CERRADOS ----
    @action(detail=False, methods=['get'], url_path='count/open/(?P<user_id>\d+)')
    def count_open(self, request, user_id=None):
        total = Ticket.objects.filter(user_id=user_id).exclude(status="Cerrado").count()
        return Response({
            "user": user_id,
            "tickets_abiertos_o_en_proceso": total
        })
    
    @action(detail=False, methods=['get'], url_path='count-open')
    def ticket_count_open_user(self, request):
        user = request.user

        count = Ticket.objects.filter(
            usuario=user
        ).exclude(
            estado="Cerrado"
        ).count()

        return Response({
            "usuario": user.id,
            "tickets_abiertos_o_en_proceso": count
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path="ticketsbyuserl")
    def ticketsbyuser(self, request):
        user = request.user  # Usuario logeado

        tickets = Ticket.objects.filter(user=user)

        serializer = self.get_serializer(tickets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
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

    @action(detail=False, methods=['get'], url_path='user_ticket_counts')
    def user_ticket_counts(self, request):
        """
        Cuenta los tickets no cerrados por usuario, filtrando solo los de la
        compañía del usuario logeado.

        Endpoint: /api/companies/user_ticket_counts/
        """
        # 1. Validación de usuario y compañía
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required.'}, status=401)
        
        # Obtener el ID de la compañía del usuario logeado
        # Esto asume que el modelo User tiene un campo de relación directa a Company (e.g., user.company_id)
        try:
            user_company_id = user.company_id 
        except AttributeError:
             # Fallback si el campo de la relación se llama 'company'
            try:
                user_company_id = user.company.id
            except AttributeError:
                # Si el usuario no tiene una compañía asociada, se devuelve un error.
                return Response({'error': 'User is not associated with a company.'}, status=403)


        # 2. Query para contar tickets
        
        # Filtros: 
        # a) company_id debe coincidir con la del usuario logeado.
        # b) status no debe ser 'cerrado'.
        ticket_counts = Ticket.objects.filter(
            company_id=user_company_id
        ).exclude(
            status='cerrado'
        ).values(
            # Agrupar por el usuario que creó el ticket, y obtener su nombre de usuario
            # Usamos 'user' (FK field) y 'user__username' para información extra.
            'user', 
            'user__username'
        ).annotate(
            # Contar el número de tickets en cada grupo
            open_ticket_count=Count('user')
        ).order_by('-open_ticket_count')

        # 3. Retornar la respuesta
        # DRF convierte el QuerySet resultante a JSON automáticamente.
        return Response(list(ticket_counts))
    
    #Funcion para exportar ticket a PDF

    @action(detail=True, methods=['get'], url_path='export-pdf')
    def export_pdf(self, request, pk=None):
        try:
            ticket = self.get_object()
    
            # Buscar reportes del ticket
            reportes = Report.objects.filter(ticket=ticket)
    
            # Crear PDF en memoria
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="ticket_{ticket.id}.pdf"'
    
            p = canvas.Canvas(response, pagesize=letter)
            width, height = letter
            y = height - 50
    
            # ---------------------------
            # TÍTULO
            # ---------------------------
            p.setFont("Helvetica-Bold", 18)
            p.drawString(50, y, f"Reporte del Ticket #{ticket.id}")
            y -= 30
    
            # ---------------------------
            # INFORMACIÓN DEL TICKET
            # ---------------------------
            p.setFont("Helvetica-Bold", 14)
            p.drawString(50, y, "Información del Ticket")
            y -= 20
    
            p.setFont("Helvetica", 12)
            p.drawString(50, y, f"Título: {ticket.title}")
            y -= 15
            p.drawString(50, y, f"Descripción: {ticket.description or 'N/A'}")
            y -= 15
            p.drawString(50, y, f"Estado: {ticket.status}")
            y -= 15
            p.drawString(50, y, f"Categoría: {ticket.category}")
            y -= 15
            p.drawString(50, y, f"Prioridad: {ticket.priority}")
            y -= 15
    
            if ticket.location:
                p.drawString(50, y, f"Ubicación: {ticket.location.name}")
                y -= 15
    
            p.drawString(50, y, f"Equipo: {ticket.equipment or 'N/A'}")
            y -= 30
    
            # ---------------------------
            # REPORTES
            # ---------------------------
            for rpt in reportes:
            
                if y < 100:
                    p.showPage()
                    y = height - 50
    
                p.setFont("Helvetica-Bold", 14)
                p.drawString(50, y, f"Reporte #{rpt.id} - Fecha: {rpt.created_at}")
                y -= 25
    
                # ---------------------------
                # MENSAJES DEL REPORTE
                # ---------------------------
                mensajes = ReportMessage.objects.filter(report=rpt)
    
                p.setFont("Helvetica-Bold", 12)
                p.drawString(50, y, "Mensajes:")
                y -= 20
    
                if not mensajes.exists():
                    p.setFont("Helvetica", 11)
                    p.drawString(70, y, "- Sin mensajes")
                    y -= 20
                    continue
                
                for msg in mensajes:
                
                    if y < 120:
                        p.showPage()
                        y = height - 50
    
                    # Texto del mensaje
                    p.setFont("Helvetica", 11)
                    p.drawString(70, y, f"- {msg.created_at}: {msg.message}")
                    y -= 15
    
                    # Imagen si existe
                    if msg.image:
                        try:
                            img_path = msg.image.path
                            p.drawImage(img_path, 70, y - 120, width=150, height=120)
                            y -= 140
                        except Exception:
                            p.drawString(70, y, "(Error al cargar imagen)")
                            y -= 20
    
                    y -= 10
    
            p.showPage()
            p.save()
    
            return response
    
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )