from rest_framework import viewsets, status
from .models import Report, ReportMessage
from .serializers import ReportSerializer, ReportMessageSerializer, AddReportMessageSerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from tickets.models import Ticket
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from tickets.permissions import CompanyAccessPermission
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse

class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    permission_classes = [CompanyAccessPermission]

    def get_queryset(self):
        user = self.request.user

        # 1. Super Admin: Ve todos los reportes
        if user.user_type == "super_admin":
            return Report.objects.all()

        # 2. Admin: Ve todos los reportes de su propia compañía
        if user.user_type == "admin":
            # CORREGIDO: Usar ticket__company
            return Report.objects.filter(ticket__company=user.company)
            
        # 3. Normal User: Solo ve los reportes de los tickets que él mismo ha creado
        if user.user_type == "normal_user":
            # CORREGIDO: Usar ticket__user
            return Report.objects.filter(ticket__user=user)
            
        # Caso por defecto 
        return Report.objects.none()

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
    
    @action(detail=True, methods=['get'], url_path='export-pdf')
    def export_pdf(self, request, pk=None):
        try:
            # OBTENEMOS EL REPORTE ESPECÍFICO A TRAVÉS DE SU PK
            reporte_base = self.get_object() 
            ticket = reporte_base.ticket # Accedemos al Ticket relacionado
            
            # --- El resto de la lógica es similar, pero ahora centrada en el reporte_base ---

            # Crear PDF en memoria
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="reporte_{reporte_base.id}_ticket_{ticket.id}.pdf"'
    
            p = canvas.Canvas(response, pagesize=letter)
            width, height = letter
            y = height - 50
    
            # ---------------------------
            # TÍTULO
            # ---------------------------
            p.setFont("Helvetica-Bold", 18)
            p.drawString(50, y, f"Reporte #{reporte_base.id} del Ticket #{ticket.id}")
            y -= 30
    
            # ---------------------------
            # INFORMACIÓN DEL TICKET Y USUARIO
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
            p.drawString(50, y, f"Prioridad: {ticket.priority}")
            y -= 15
            
            # Información del usuario
            p.drawString(50, y, f"Creado por: {ticket.user.get_full_name() or ticket.user.email}")
            y -= 15

            if ticket.location:
                p.drawString(50, y, f"Ubicación: {ticket.location.name}")
                y -= 15
    
            p.drawString(50, y, f"Equipo: {ticket.equipment or 'N/A'}")
            y -= 30
    
            # ---------------------------
            # CONTENIDO DEL REPORTE ESPECÍFICO
            # ---------------------------
            
            # Solo iteramos sobre el reporte_base que acabamos de obtener
            rpt = reporte_base
        
            if y < 100:
                p.showPage()
                y = height - 50

            p.setFont("Helvetica-Bold", 14)
            p.drawString(50, y, f"Reporte #{rpt.id} - Fecha: {rpt.created_at.strftime('%Y-%m-%d %H:%M')}")
            y -= 25

            # ---------------------------
            # MENSAJES DEL REPORTE
            # ---------------------------
            mensajes = ReportMessage.objects.filter(report=rpt).order_by('created_at')

            p.setFont("Helvetica-Bold", 12)
            p.drawString(50, y, "Mensajes:")
            y -= 20

            if not mensajes.exists():
                p.setFont("Helvetica", 11)
                p.drawString(70, y, "- Sin mensajes")
                y -= 20
            
            for msg in mensajes:
            
                if y < 120:
                    p.showPage()
                    y = height - 50

                # Texto del mensaje
                p.setFont("Helvetica", 11)
                p.drawString(70, y, f"- {msg.created_at.strftime('%H:%M')}: {msg.message}")
                y -= 15

                # Imagen si existe
                if msg.image:
                    try:
                        img_path = msg.image.path
                        # Ajusta las dimensiones y la posición según sea necesario
                        p.drawImage(img_path, 70, y - 120, width=150, height=120, preserveAspectRatio=True, anchor='n')
                        y -= 140
                    except Exception as img_e:
                        p.drawString(70, y, "(Error al cargar imagen o ruta inaccesible)")
                        y -= 20

                y -= 10
    
            p.showPage()
            p.save()
    
            return response
    
        except Report.DoesNotExist:
            return Response(
                {"error": "Reporte no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            # Considera logging de errores más robusto aquí
            return Response(
                {"error": f"Ocurrió un error interno al generar el PDF: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class ReportMessageViewSet(viewsets.ModelViewSet):
    # 1. PERMISOS: Solo permite el acceso a usuarios que han iniciado sesión.
    # No aplica filtros de compañía o de objeto.
    permission_classes = [IsAuthenticated] 
    
    serializer_class = ReportMessageSerializer
    queryset = ReportMessage.objects.all() # Todos los mensajes