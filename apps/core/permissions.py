from rest_framework import permissions
from apps.core.models import BusinessMember


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

        try:
            member = BusinessMember.objects.get(
                business=business, user=request.user, is_active=True
            )
            return member.role in ["owner", "admin"]
        except BusinessMember.DoesNotExist:
            return False


class IsBusinessOwner(permissions.BasePermission):
    """
    Solo el owner del negocio (para operaciones críticas).
    """

    def has_object_permission(self, request, view, obj):
        business = getattr(obj, "business", None)
        if not business:
            return False

        if request.user.is_staff:
            return True

        try:
            member = BusinessMember.objects.get(
                business=business, user=request.user, is_active=True
            )
            return member.role == "owner"
        except BusinessMember.DoesNotExist:
            return False


class IsSameUserOrAdmin(permissions.BasePermission):
    """
    El usuario solo puede editar su propia información o ser admin.
    """

    def has_object_permission(self, request, view, obj):
        # Staff puede ver/editar cualquier usuario
        if request.user.is_staff:
            return True

        # El usuario puede ver/editar su propia info
        if hasattr(obj, "user"):
            return obj.user == request.user
        return obj == request.user


class CanManageCustomers(permissions.BasePermission):
    """
    Permiso para gestionar clientes del negocio.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Si hay business_id en los params, verificar membresía
        business_id = request.data.get("business") or request.query_params.get(
            "business"
        )

        if business_id:
            return BusinessMember.objects.filter(
                business_id=business_id,
                user=request.user,
                is_active=True,
                role__in=["owner", "admin", "manager"],
            ).exists()

        return True  # Para listar, filtraremos en el queryset


class CanManageOrders(permissions.BasePermission):
    """
    Permiso para gestionar órdenes del negocio.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        business_id = request.data.get("business") or request.query_params.get(
            "business"
        )

        if business_id:
            return BusinessMember.objects.filter(
                business_id=business_id,
                user=request.user,
                is_active=True,
                role__in=["owner", "admin", "manager", "employee", "cashier"],
            ).exists()

        return True


class CanViewFinance(permissions.BasePermission):
    """
    Permiso para ver información financiera.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        business_id = request.query_params.get("business")

        if business_id:
            return BusinessMember.objects.filter(
                business_id=business_id,
                user=request.user,
                is_active=True,
                role__in=["owner", "admin"],
            ).exists()

        return request.user.is_staff


# ✅ Mixin mejorado para filtrar por negocio automáticamente
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

        # Filtrar por business_id si viene en los params
        business_id = self.request.query_params.get("business")
        if business_id:
            # Verificar que el usuario sea miembro de ese negocio
            is_member = BusinessMember.objects.filter(
                business_id=business_id, user=user, is_active=True
            ).exists()

            if is_member:
                return queryset.filter(business_id=business_id)
            else:
                return queryset.none()  # No tiene acceso

        # Si no hay business_id, mostrar de todos sus negocios
        user_businesses = BusinessMember.objects.filter(
            user=user, is_active=True
        ).values_list("business_id", flat=True)

        return queryset.filter(business_id__in=user_businesses)
