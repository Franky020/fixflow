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