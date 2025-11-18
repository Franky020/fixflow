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

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    # permission_classes = [IsAuthenticated]

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
    
            # Título del PDF
            p.setFont("Helvetica-Bold", 16)
            p.drawString(50, y, f"Reporte del Ticket #{ticket.id}")
            y -= 30
    
            # Información del Ticket
            p.setFont("Helvetica", 12)
            p.drawString(50, y, f"Título: {ticket.titulo}")
            y -= 20
            p.drawString(50, y, f"Descripción: {ticket.descripcion}")
            y -= 20
            p.drawString(50, y, f"Estado: {ticket.estado}")
            y -= 30
    
            # Loop por reportes
            for rpt in reportes:
                p.setFont("Helvetica-Bold", 14)
                p.drawString(50, y, f"Reporte #{rpt.id}")
                y -= 20
    
                p.setFont("Helvetica", 12)
                p.drawString(50, y, f"Descripción: {rpt.descripcion}")
                y -= 20
                p.drawString(50, y, f"Fecha: {rpt.fecha_creacion}")
                y -= 20
    
                # Mensajes del reporte
                mensajes = Message.objects.filter(reporte=rpt)
    
                p.setFont("Helvetica-Bold", 12)
                p.drawString(50, y, "Mensajes:")
                y -= 20
    
                for msg in mensajes:
                    if y < 80:
                        p.showPage()
                        y = height - 80
    
                    p.setFont("Helvetica", 11)
                    p.drawString(70, y, f"- {msg.usuario.username}: {msg.texto}")
                    y -= 15
    
                y -= 15
    
                if y < 80:
                    p.showPage()
                    y = height - 80
    
            p.showPage()
            p.save()
    
            return response
    
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )