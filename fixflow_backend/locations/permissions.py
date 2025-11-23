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

        # Si el objeto tiene company, comparamos
        if hasattr(obj, "company"):
            return obj.company_id == user.company_id

        return False