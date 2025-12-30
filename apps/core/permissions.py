from rest_framework import permissions


class IsBusinessMemberOrReadOnly(permissions.BasePermission):
    """
    Permiso: Solo miembros del negocio pueden modificar.
    Otros pueden ver si es público.
    """

    def has_permission(self, request, view):
        # Usuarios autenticados pueden hacer GET
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Para POST/PUT/DELETE, verificar membresía
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Obtener el business del objeto
        business = getattr(obj, "business", None)
        if not business:
            return False

        # Staff puede hacer todo
        if request.user.is_staff:
            return True

        # Verificar si el usuario es miembro del negocio
        from apps.core.models import BusinessMember

        is_member = BusinessMember.objects.filter(
            business=business, user=request.user, is_active=True
        ).exists()

        # Permitir lectura a miembros
        if request.method in permissions.SAFE_METHODS:
            return is_member

        # Modificaciones solo para admin/owner
        if is_member:
            member = BusinessMember.objects.get(business=business, user=request.user)
            return member.role in ["owner", "admin"]

        return False


class IsBusinessOwnerOrAdmin(permissions.BasePermission):
    """
    Solo el owner o admin del negocio puede hacer cambios críticos.
    """

    def has_object_permission(self, request, view, obj):
        business = getattr(obj, "business", None)
        if not business:
            return False

        if request.user.is_staff:
            return True

        from apps.core.models import BusinessMember

        try:
            member = BusinessMember.objects.get(
                business=business, user=request.user, is_active=True
            )
            return member.role in ["owner", "admin"]
        except BusinessMember.DoesNotExist:
            return False


# Mixin para filtrar por negocio automáticamente
class BusinessFilterMixin:
    """
    Mixin que filtra automáticamente por negocios del usuario.
    """

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # Staff ve todo
        if user.is_staff:
            return queryset

        # Usuarios normales solo ven datos de sus negocios
        from apps.core.models import BusinessMember

        user_businesses = BusinessMember.objects.filter(
            user=user, is_active=True
        ).values_list("business_id", flat=True)

        return queryset.filter(business_id__in=user_businesses)
