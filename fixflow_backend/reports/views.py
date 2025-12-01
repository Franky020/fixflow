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
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from io import BytesIO
import os
import requests
class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated] 

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
            # 1. OBTENEMOS EL REPORTE ESPECÍFICO
            reporte_base = self.get_object() 
            ticket = reporte_base.ticket # Accedemos al Ticket relacionado
            
            # --- CONFIGURACIÓN DEL DOCUMENTO ---
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="reporte_{reporte_base.id}_ticket_{ticket.id}.pdf"'

            # Usar SimpleDocTemplate para estructura avanzada y auto-paginación
            doc = SimpleDocTemplate(response, 
                                    pagesize=letter, 
                                    rightMargin=40, 
                                    leftMargin=40, 
                                    topMargin=60, 
                                    bottomMargin=40)
            elements = []

            # --- ESTILOS ---
            styles = getSampleStyleSheet()
            style_normal = styles['Normal']
            
            style_title = ParagraphStyle(
                'Title',
                parent=styles['Title'],
                alignment=2,  # Derecha
                fontSize=18,
                textColor=colors.HexColor("#076c77"), # Color principal
                spaceAfter=6
            )
            # Título de sección centrado con fondo gris
            style_box_title_centered = ParagraphStyle(
                'BoxTitleCentered',
                parent=styles['Heading3'],
                backColor=colors.lightgrey,
                textColor=colors.black,
                fontSize=12,
                spaceAfter=6,
                spaceBefore=12,
                alignment=1,  # Centrado
            )
            # Estilo para el contenido de las tablas (dentro de las celdas)
            style_content = ParagraphStyle('Content', parent=style_normal, fontSize=10, leading=12)

            # --- ENCABEZADO: LOGO Y TÍTULO ---
            logo_path = os.path.join("static", "logo.png") # Ruta local para el logo
            header_row = []
            
            # 1. Columna del Logo (Izquierda)
            if os.path.exists(logo_path):
                img = RLImage(logo_path, width=120, height=50)
                img.hAlign = 'LEFT'
                header_row.append(img)
            else:
                header_row.append(Paragraph("<b>[LOGO FALTANTE]</b>", style_normal))

            # 2. Columna del Título (Derecha)
            ubicacion_nombre = getattr(ticket.location, 'name', 'N/A')
            titulo_paragraph = Paragraph(f"<b>Reporte #{reporte_base.id}</b><br/><font size='10'>Ubicación: {ubicacion_nombre}</font>", style_title)
            header_row.append(titulo_paragraph)

            header_table = Table([header_row], colWidths=[200, 300])
            header_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ]))
            elements.append(header_table)
            elements.append(Spacer(1, 12))

            # --- SECCIÓN: INFORMACIÓN DEL TICKET ---
            elements.append(Paragraph("Información del Ticket", style_box_title_centered))

            info_data = [
                ['Título:', ticket.title],
                ['Descripción:', ticket.description or 'N/A'],
                ['Estado:', ticket.status],
                ['Prioridad:', ticket.priority],
                ['Creado por:', ticket.user.get_full_name() or ticket.user.email],
                ['Equipo:', ticket.equipment or 'N/A'],
            ]
            info_table = Table(info_data, colWidths=[130, 350])
            info_table.setStyle(TableStyle([
                ('BOX', (0,0), (-1,-1), 1, colors.black),  # Borde completo
                ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'), # Primera columna en negrita
                ('FONTNAME', (1,0), (-1,-1), 'Helvetica'),
                ('FONTSIZE', (0,0), (-1,-1), 10),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
            ]))
            elements.append(info_table)
            elements.append(Spacer(1, 12))

            # --- SECCIÓN: MENSAJES Y EVIDENCIA ---
            elements.append(Paragraph(f"Mensajes y Evidencia (Reporte #{reporte_base.id})", style_box_title_centered))
            
            mensajes = ReportMessage.objects.filter(report=reporte_base).order_by('created_at')

            if not mensajes.exists():
                elements.append(Paragraph("No hay mensajes asociados a este reporte.", style_content))
            else:
                for msg in mensajes:
                    # 1. LÍNEA DE TEXTO (Fecha y Mensaje)
                    fecha_msg = msg.created_at.strftime('%Y-%m-%d %H:%M')
                    contenido_msg = msg.message if msg.message else "(Sin mensaje de texto)"
                    
                    elements.append(Paragraph(f"<b>[{fecha_msg}]</b>: {contenido_msg}", style_content))
                    
                    # 2. IMAGEN (Si existe) - Ahora usa la URL de Cloudinary
                    if msg.image:
                        try:
                            # 🚨 CLAVE: Usamos .url en lugar de .path y descargamos
                            img_url = msg.image.url 
                            r = requests.get(img_url, stream=True)
                            
                            if r.status_code == 200:
                                img_data = BytesIO(r.content)
                                # Usamos RLImage con el buffer de datos
                                rl_img = RLImage(img_data, width=200, height=150)
                                rl_img.hAlign = 'CENTER' # Centramos la imagen
                                elements.append(rl_img)
                            else:
                                elements.append(Paragraph(f"<i>(Error al descargar imagen: {r.status_code})</i>", style_content))
                        except Exception as img_e:
                            elements.append(Paragraph(f"<i>(Error al cargar imagen: {str(img_e)})</i>", style_content))

                    elements.append(Spacer(1, 8)) # Espacio entre mensajes

            # --- SECCIÓN: FIRMA Y FOOTER ---
            elements.append(Spacer(1, 40))
            elements.append(Paragraph("______________________________", style_normal))
            elements.append(Paragraph("Firma", style_normal))
            elements.append(Spacer(1, 12))
            
            elements.append(Spacer(1, 40))
            elements.append(Paragraph("FixFlow - Sistema de Gestión Técnica", style_normal))
            
            # --- CONSTRUIR DOCUMENTO ---
            doc.build(elements)
            return response
        
        except Report.DoesNotExist:
            return Response(
                {"error": "Reporte no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
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