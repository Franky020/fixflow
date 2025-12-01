from rest_framework.permissions import BasePermission

class CompanyAccessPermission(BasePermission):
    """
    - super_admin -> ve TODO
    - admin / normal_user -> solo objetos de SU compañía
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user

        # super_admin siempre puede ver todo
        if user.user_type == "super_admin":
            return True

        if hasattr(obj, "ticket") and hasattr(obj.ticket, "company"):
            object_company_id = obj.ticket.company_id

        # CASO 3: El objeto es un ReportMessage (Relación: ReportMessage -> Report -> Ticket -> Company)
        # Se accede a través del campo 'report', y luego 'ticket'
        elif hasattr(obj, "report") and hasattr(obj.report, "ticket") and hasattr(obj.report.ticket, "company"):
            object_company_id = obj.report.ticket.company_id
        
        # -----------------------------------------------------------
        
        # Si logramos obtener una company_id válida
        if object_company_id is not None:
            # 2. Comparamos la compañía del objeto con la compañía del usuario
            return object_company_id == user.company_id

        # 3. Si no se pudo determinar la compañía del objeto, negamos el acceso por seguridad
        return False