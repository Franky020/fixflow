from rest_framework import viewsets, status
from .models import Report, ReportMessage
from .serializers import ReportSerializer, ReportMessageSerializer, AddReportMessageSerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from tickets.models import Ticket

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer

    @action(detail=True, methods=['post'], url_path='add-message')
    def add_message(self, request, pk=None):
        report = self.get_object()

        # Validar los campos del formulario (para que DRF los muestre)
        serializer = AddReportMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        text = serializer.validated_data["message"]
        image = serializer.validated_data.get("image")

        message = ReportMessage.objects.create(
            report=report,
            message=text,
            image=image
        )

        return Response(ReportMessageSerializer(message).data, status=201)

    @action(detail=False, methods=['get'], url_path="reportes-by-user")
    def reportes_by_user(self, request):
        user = request.user  # Usuario logeado

        # Primero obtenemos los tickets del usuario
        tickets_del_usuario = Ticket.objects.filter(user=user)

        # Luego buscamos los reportes ligados a esos tickets
        reports = Report.objects.filter(ticket__in=tickets_del_usuario)

        # Serializamos
        serializer = ReportSerializer(reports, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='messages')
    def get_messages(self, request, pk=None):
        try:
            report = self.get_object()  # obtiene el reporte por ID
        except Report.DoesNotExist:
            return Response({"error": "Reporte no encontrado"}, status=404)

        mensajes = report.messages.all()  # gracias al related_name="messages"

        serializer = ReportMessageSerializer(mensajes, many=True)
        return Response(serializer.data, status=200)


class ReportMessageViewSet(viewsets.ModelViewSet):
    queryset = ReportMessage.objects.all()
    serializer_class = ReportMessageSerializer