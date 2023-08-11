from rest_framework import serializers
from .models import User, Subscription
from django.core.exceptions import ValidationError
from django.core.validators import validate_email


class UserSerializer(serializers.ModelSerializer):
    followers_count = serializers.SerializerMethodField()
    subscriptions_count = serializers.SerializerMethodField()
    subscribed_creators_ids = serializers.SerializerMethodField()

    def get_followers_count(self, obj):
        return obj.get_followers_count()

    def get_subscriptions_count(self, obj):
        return obj.get_subscriptions_count()

    def get_subscribed_creators_ids(self, obj):
        return obj.get_subscribed_creators_ids()

    def get_subscriptions(self, obj):  # Nouvelle méthode pour récupérer les abonnements
        if obj.is_creator:
            subscriptions = obj.subscriptions.all()
            return SubscriptionSerializer(subscriptions, many=True).data
        return []

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "telephone",
            "email",
            "last_name",
            "first_name",
            "image",
            "user_type",
            "is_active",
            "is_verified",
            "is_staff",
            "is_superuser",
            "interests",
            "expertise",
            "is_creator",
            "subscription_expiry",
            "subscription_active",
            "followers_count",
            "subscriptions_count",
            "subscribed_creators_ids",
        )
        extra_kwargs = {
            "image": {"required": False},
        }


class UserPhotoUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("image",)


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def validate_username(self, value):
        # Ajoutez ici la logique de validation pour le champ "username"
        if len(value) < 3:
            raise serializers.ValidationError(
                "Le nom d'utilisateur doit contenir au moins 3 caractères."
            )
        return value

    def validate_email(self, value):
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError(
                "Veuillez fournir une adresse e-mail valide."
            )

        return value

    def validate_password(self, value):
        # Ajoutez ici la logique de validation pour le champ "password"
        if len(value) < 8:
            raise serializers.ValidationError(
                "Le mot de passe doit contenir au moins 8 caractères."
            )
        return value


class ResetPasswordEmailRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=2)

    class Meta:
        field = ["email"]


class PasswordResetSerializer(serializers.Serializer):
    verification_code = serializers.CharField()
    new_password1 = serializers.CharField(write_only=True)
    new_password2 = serializers.CharField(write_only=True)

    def validate(self, data):
        new_password1 = data.get("new_password1")
        new_password2 = data.get("new_password2")

        if new_password1 != new_password2:
            raise serializers.ValidationError(
                "Les nouveaux mots de passe ne correspondent pas."
            )

        return data


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            raise serializers.ValidationError(
                "Veuillez saisir un nom d'utilisateur et un mot de passe."
            )

        return data


class SubscriptionSerializer(serializers.ModelSerializer):
    subscriber = serializers.PrimaryKeyRelatedField(read_only=True)
    creator = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_creator=True)
    )
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ["id", "subscriber", "creator", "is_subscribed"]

    def get_is_subscribed(self, obj):
        # Vérifie si l'utilisateur actuel est abonné au créateur de l'abonnement
        request_user = self.context["request"].user
        return obj.subscriber == request_user

    def create(self, validated_data):
        # Crée un nouvel abonnement en utilisant les données validées et l'utilisateur actuel
        request_user = self.context["request"].user
        validated_data["subscriber"] = request_user
        return Subscription.objects.create(**validated_data)
