from rest_framework import serializers
from django.contrib.auth import authenticate
from apps.core.models import User


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer para registro de nuevos usuarios
    """

    password = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}, min_length=8
    )
    password_confirm = serializers.CharField(
        write_only=True, required=True, style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "phone",
            "user_type",
        ]
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate(self, attrs):
        """Validar que las contraseñas coincidan"""
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password": "Las contraseñas no coinciden"}
            )
        return attrs

    def create(self, validated_data):
        """Crear nuevo usuario"""
        # Remover password_confirm
        validated_data.pop("password_confirm")

        # Crear usuario
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            phone=validated_data.get("phone", ""),
            user_type=validated_data.get("user_type", "customer"),
        )
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer para login de usuarios
    """

    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}
    )

    def validate(self, attrs):
        """Validar credenciales"""
        email = attrs.get("email")
        password = attrs.get("password")

        if email and password:
            # Autenticar usuario
            user = authenticate(
                request=self.context.get("request"),
                username=email,  # Django usa 'username' internamente
                password=password,
            )

            if not user:
                raise serializers.ValidationError(
                    "Email o contraseña incorrectos", code="authorization"
                )

            if not user.is_active:
                raise serializers.ValidationError(
                    "Esta cuenta está desactivada", code="authorization"
                )

            attrs["user"] = user
            return attrs
        else:
            raise serializers.ValidationError(
                "Debe proporcionar email y contraseña", code="authorization"
            )


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar información del usuario autenticado
    """

    full_name = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "phone",
            "avatar",
            "user_type",
            "email_verified",
            "phone_verified",
            "is_active",
            "date_joined",
        ]
        read_only_fields = [
            "id",
            "email",
            "user_type",
            "email_verified",
            "phone_verified",
            "is_active",
            "date_joined",
        ]


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer para cambiar contraseña
    """

    old_password = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}
    )
    new_password = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}, min_length=8
    )
    new_password_confirm = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}
    )

    def validate(self, attrs):
        """Validar contraseñas"""
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password": "Las contraseñas no coinciden"}
            )
        return attrs

    def validate_old_password(self, value):
        """Validar contraseña actual"""
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Contraseña incorrecta")
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer para solicitar reset de contraseña
    """

    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """Verificar que el email existe"""
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            # Por seguridad, no revelar si el email existe
            pass
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer para confirmar reset de contraseña
    """

    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}, min_length=8
    )
    new_password_confirm = serializers.CharField(
        required=True, write_only=True, style={"input_type": "password"}
    )

    def validate(self, attrs):
        """Validar contraseñas"""
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password": "Las contraseñas no coinciden"}
            )
        return attrs
