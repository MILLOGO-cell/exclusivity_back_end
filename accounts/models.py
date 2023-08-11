from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils.text import slugify
from django.contrib.auth.tokens import PasswordResetTokenGenerator
import uuid
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model


class UserManager(BaseUserManager):
    def create_user(
        self, email, username, password=None, user_type="visitor", **extra_fields
    ):
        if username is None:
            raise TypeError("Le champs nom d'utilisateur est obligatoire.")
        if not email:
            raise ValueError("L'email est obligatoire.")

        email = self.normalize_email(email)
        user = self.model(
            email=email, username=username, user_type=user_type, **extra_fields
        )
        user.set_password(password)

        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault("user_type", "admin")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(
            email=email, username=username, password=password, **extra_fields
        )


class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return str(user.pk) + user.email + str(timestamp) + str(user.is_active)


token_generator = TokenGenerator()


class User(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = (
        ("admin", "Administrateur"),
        ("creator", "Créateur"),
        ("visitor", "Visiteur"),
    )
    username = models.CharField(max_length=150, blank=True, null=True, unique=True)
    telephone = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(unique=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to="user_images/", null=True, blank=True)
    user_type = models.CharField(
        max_length=10, choices=USER_TYPE_CHOICES, default="visitor"
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    verification_code_expiration = models.DateTimeField(null=True, blank=True)
    is_superuser = models.BooleanField(default=False)
    interests = models.CharField(max_length=255, blank=True)
    expertise = models.CharField(max_length=255, blank=True)
    is_creator = models.BooleanField(default=False)
    subscription_expiry = models.DateTimeField(null=True, blank=True)
    subscription_active = models.BooleanField(default=False)
    activation_token = models.UUIDField(default=uuid.uuid4, editable=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    objects = UserManager()

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser

    def change_user_type(self, new_user_type):
        self.user_type = new_user_type
        self.save()

    def is_subscriber(self):
        return (
            self.is_creator
            and self.subscription_active
            and self.subscription_expiry is not None
        )

    def get_subscribers(self):
        if self.is_creator:
            return self.subscriptions.all()
        return User.objects.none()

    def generate_username(self, email):
        username = email.split("@")[0]
        return username

    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {"refresh": str(refresh), "access": str(refresh.access_token)}

    def generate_password_reset_token(self):
        """
        Génère un token pour la récupération du mot de passe.
        """
        return token_generator.make_token(self)

    def activate_account(self, token):
        """
        Active le compte utilisateur à partir du token d'activation.
        Retourne True si l'activation réussit, False sinon.
        """
        if token_generator.check_token(self, token):
            self.is_verified = True
            self.save()
            return True
        return False

    def reset_password(self, token, new_password):
        """
        Réinitialise le mot de passe de l'utilisateur à partir du token de récupération.
        Retourne True si la réinitialisation réussit, False sinon.
        """
        if token_generator.check_token(self, token):
            self.set_password(new_password)
            self.save()
            return True
        return False

    def get_subscriptions_count(self):
        return self.user_subscriptions.count()

    def get_subscriptions_details(self):
        return self.user_subscriptions.all()

    # Méthodes pour les abonnés d'un créateur
    def get_followers_count(self):
        if self.is_creator:
            return self.user_followers.count()
        return 0

    def get_followers_details(self):
        return self.subscribers.all()

    def get_subscribed_creators_ids(self):
        if not self.is_creator:
            return self.user_subscriptions.values_list("creator_id", flat=True)
        return []


class Subscription(models.Model):
    subscriber = models.ForeignKey(
        get_user_model(), related_name="user_subscriptions", on_delete=models.CASCADE
    )
    creator = models.ForeignKey(
        get_user_model(), related_name="user_followers", on_delete=models.CASCADE
    )
    Subscription_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subscriber.email} s'abonne à {self.creator.email}"

    class Meta:
        verbose_name = "Abonnement"  # Nom en français pour le modèle
        verbose_name_plural = "Abonnements"
