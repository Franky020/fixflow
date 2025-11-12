from django.shortcuts import render
from rest_framework import viewsets
from .models import Ticket
from .serializers import TicketSerializer
from django.conf import settings
import requests

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

    def send_notification(self, ticket):
        if not ticket.user.device_token:
            print("No device token for user.")
            return

        fcm_url = "https://fcm.googleapis.com/fcm/send"
        headers = {
            "Authorization": f"key={settings.FCM_SERVER_KEY}",
            "Content-Type": "application/json"
        }
        body = {
            "to": ticket.user.device_token,
            "notification": {
                "title": f"Nuevo Ticket: {ticket.title}",
                "body": f"{ticket.description or 'Tienes un nuevo ticket asignado.'}"
            },
            "data": {
                "ticket_id": ticket.id,
                "priority": ticket.priority,
                "category": ticket.category
            }
        }

        response = requests.post(fcm_url, headers=headers, json=body)
        print("Notificación enviada:", response.json())