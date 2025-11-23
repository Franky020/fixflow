from rest_framework.permissions import BasePermission

class CompanyAccessPermission(BasePermission):
    """
    Permiso universal:
    
    - super_admin -> puede ver TODO
    - admin / normal_user -> solo objetos de SU compañía
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        # super_admin ve todo
        if user.user_type == "super_admin":
            return True

        # objetos con compañía
        if hasattr(obj, "company"):
            return obj.company == user.company

        return False