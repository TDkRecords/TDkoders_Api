from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework import status, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from .serializers import (
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)

User = get_user_model()


class AuthViewSet(viewsets.ViewSet):
    """
    ViewSet centralizado para autenticación
    """

    # 🔐 REGISTER
    @action(detail=False, methods=["post"], permission_classes=[permissions.AllowAny])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": UserSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_201_CREATED,
        )

    # 🔑 LOGIN
    @action(detail=False, methods=["post"], permission_classes=[permissions.AllowAny])
    def login(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        # Ahora validated_data SÍ tiene user, refresh, access
        user = serializer.validated_data["user"]

        # Obtener negocios del usuario
        from apps.core.models import BusinessMember

        businesses = (
            BusinessMember.objects.filter(user=user, is_active=True)
            .select_related("business")
            .values("business__id", "business__name", "business__slug", "role")
        )

        return Response(
            {
                "user": UserSerializer(user).data,
                "refresh": serializer.validated_data["refresh"],
                "access": serializer.validated_data["access"],
                "businesses": list(businesses),  # ← Esto es CLAVE para el frontend
            },
            status=status.HTTP_200_OK,
        )

    # 🚪 LOGOUT (blacklist refresh token)
    @action(
        detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def logout(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    # 👤 ME
    @action(
        detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def me(self, request):
        return Response(UserSerializer(request.user).data)

    # 🔒 CHANGE PASSWORD
    @action(
        detail=False, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def change_password(self, request):
        user = request.user
        serializer = ChangePasswordSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        if not user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"old_password": ["Wrong password."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response(
            {
                "status": "success",
                "message": "Password updated successfully",
            },
            status=status.HTTP_200_OK,
        )

    # 📧 PASSWORD RESET REQUEST
    @action(detail=False, methods=["post"], permission_classes=[permissions.AllowAny])
    def password_reset(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        user = User.objects.get(email=email)

        # ⚠️ Ejemplo simplificado
        token = "sample_reset_token"
        reset_url = f"{settings.FRONTEND_URL}/reset-password/confirm/?uid={user.id}&token={token}"

        return Response(
            {"detail": "Password reset e-mail has been sent."},
            status=status.HTTP_200_OK,
        )

    # ✅ PASSWORD RESET CONFIRM
    @action(detail=False, methods=["post"], permission_classes=[permissions.AllowAny])
    def password_reset_confirm(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            uid = serializer.validated_data["uid"]
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, User.DoesNotExist):
            user = None

        if not user:
            return Response(
                {"detail": "Invalid token or user ID"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response(
            {"detail": "Password has been reset successfully."},
            status=status.HTTP_200_OK,
        )
