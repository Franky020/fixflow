from rest_framework.permissions import BasePermission
from django.db.models import Q

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
             queryset = user.objects.all()

        # objetos con compañía
        else:

            queryset = user.obj.filter(company=user.company)
            