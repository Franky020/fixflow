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

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

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
        user = request.user  # usuario logeado
    
        # Filtrar solo tickets del usuario logeado
        tickets = Ticket.objects.filter(user=user)
    
        # Agrupar y contar por estado
        counts = tickets.values('status').annotate(total=Count('id'))
    
        # Si no tiene tickets
        if not tickets.exists():
            return Response(
                {"message": "El usuario no tiene tickets."},
                status=status.HTTP_404_NOT_FOUND
            )
    
        # Formato de respuesta amigable
        result = {item['status']: item['total'] for item in counts}
    
        return Response(result, status=status.HTTP_200_OK)

    # ---- CONTAR TICKETS DEL USUARIO EXCEPTO LOS CERRADOS ----
    @action(detail=False, methods=['get'], url_path='count/open/(?P<user_id>\d+)')
    def count_open(self, request, user_id=None):
        total = Ticket.objects.filter(user_id=user_id).exclude(status="Cerrado").count()
        return Response({
            "user": user_id,
            "tickets_abiertos_o_en_proceso": total
        })
    
    @api_view(['GET'])
    @permission_classes([IsAuthenticated])
    def ticket_count_open_user(request):
        user = request.user
    
        count = Ticket.objects.filter(
            usuario=user
        ).exclude(
            estado="Cerrado"
        ).count()
    
        return Response({
            "usuario": user.id,
            "tickets_abiertos_o_en_proceso": count
        })