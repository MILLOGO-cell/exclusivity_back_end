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
    username = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(unique=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    image = models.ImageField(upload_to="user_images/", null=True, blank=True)
    user_type = models.CharField(
        max_length=10, choices=USER_TYPE_CHOICES, default="visitor"
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    interests = models.CharField(max_length=255, blank=True)
    expertise = models.CharField(max_length=255, blank=True)
    is_creator = models.BooleanField(default=False)
    subscription_expiry = models.DateTimeField(null=True, blank=True)
    subscription_active = models.BooleanField(default=False)
    activation_token = models.UUIDField(default=uuid.uuid4, editable=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

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
            return User.objects.filter(subscriptions__creator=self)
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
            self.is_active = True
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
        return self.subscriptions.count()

    def get_subscriptions_details(self):
        return self.subscriptions.all()

    # Méthodes pour les abonnés d'un créateur
    def get_followers_count(self):
        return self.subscribers.count()

    def get_followers_details(self):
        return self.subscribers.all()
