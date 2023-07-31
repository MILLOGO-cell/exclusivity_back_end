from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from .models import User
from .serializers import (
    RegisterSerializer,
    ResetPasswordEmailRequestSerializer,
    PasswordResetSerializer,
    LoginSerializer,
)
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.sites.models import Site
from django.urls import reverse
from rest_framework_simplejwt.tokens import AccessToken
import uuid
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.generics import RetrieveUpdateAPIView
from .serializers import UserSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate


class UserDetailsView(RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Renvoyer l'utilisateur actuellement connecté
        return self.request.user

    def update(self, request, *args, **kwargs):
        # Vous pouvez ajouter ici un code spécifique pour la mise à jour de l'image de profil
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        # Assurez-vous que l'utilisateur actuellement connecté met à jour ses propres informations
        if instance != self.request.user:
            return Response(
                {
                    "message": "Vous n'êtes pas autorisé à mettre à jour ces informations."
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Utilisez le sérialiseur pour mettre à jour les données de l'utilisateur
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)


class CreateUserView(APIView):
    @swagger_auto_schema(request_body=RegisterSerializer)
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            username = serializer.validated_data["username"]
            password = serializer.validated_data["password"]
            user_type = serializer.validated_data.get("user_type", "visitor")

            try:
                user = User.objects.get(email=email)
                return Response(
                    {"message": "Un utilisateur avec cet email existe déjà."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except User.DoesNotExist:
                user = User.objects.create_user(
                    email=email,
                    username=username,
                    password=password,
                    user_type=user_type,
                )
                # Generate activation token
                activation_token = str(uuid.uuid4())
                user.activation_token = activation_token
                user.save()

                current_site = get_current_site(request).domain
                activation_link = f"http://{current_site}/api/utilisateurs/verification-email/{user.pk}/{activation_token}"
                send_activation_email(
                    user.username, email, activation_link
                )  # Fonction pour envoyer l'e-mail

                return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    serializer_class = LoginSerializer

    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        # Vérifier les informations d'identification de l'utilisateur
        user = authenticate(request, email=email, password=password)

        if not user:
            return Response(
                {"error": "Adresse e-mail ou mot de passe incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Générer les tokens JWT
        refresh = RefreshToken.for_user(user)
        tokens = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "id": user.id,
                "email": user.email,
            },
        }

        return Response(tokens, status=status.HTTP_200_OK)


def send_activation_email(username, email, activation_link):
    subject = "Activation de votre compte"
    message = f"""
    Bonjour {username},

    Merci de vous être inscrit sur notre plateforme. Veuillez cliquer sur le lien ci-dessous pour activer votre compte :

    {activation_link}

    Nous vous souhaitons une excellente expérience avec notre service.

    Cordialement,
    L'équipe de exclusivity.
    """
    sender = "nicolasmillogo3@gmail.com"
    recipient = email
    send_mail(subject, message, sender, [recipient])


class VerifyEmailView(APIView):
    def get(self, request, user_id, token):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {"message": "Utilisateur non trouvé."}, status=status.HTTP_404_NOT_FOUND
            )

        if str(user.activation_token) == token:
            user.is_active = True
            user.save()
            return Response(
                {"message": "Votre compte a été activé avec succès."},
                status=status.HTTP_200_OK,
            )
        else:
            print(f"Generated Token: {user.generate_activation_token()}")
            print(f"Received Token: {token}")
            return Response(
                {"message": "Le lien d'activation est invalide."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class RequestPasswordResetView(APIView):
    serializer_class = ResetPasswordEmailRequestSerializer

    @swagger_auto_schema(request_body=ResetPasswordEmailRequestSerializer)
    def post(self, request):
        email = request.data["email"]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None

        if user:
            # Generate password reset token and link
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_link = f"http://{request.get_host()}/api/reset-password/{uid}/{token}"

            # Send password reset link to user's email
            subject = "Password Reset Request"
            message = f"Bonjour  {user.username},\n\nVous pouvez réinitialiser votre mot de passe en cliquant sur le lien ci-dessous:\n\n{reset_link}\n\nSi vous n'avez pas effectué cette demande, veuillez ignorer cet e-mail.\n\nMerci,\nL'équipe Exclusivity"
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

        return Response(
            {
                "message": "Si cette adresse e-mail est valide, vous recevrez un e-mail contenant un lien pour réinitialiser votre mot de passe."
            },
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    serializer_class = PasswordResetSerializer

    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user and default_token_generator.check_token(user, token):
            serializer = PasswordResetSerializer(data=request.data)
            if serializer.is_valid():
                new_password = serializer.validated_data["new_password1"]
                user.set_password(new_password)
                user.save()
                return Response(
                    {"message": "Votre mot de passe a été réinitialisé avec succès."},
                    status=status.HTTP_200_OK,
                )

            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(
                {
                    "message": "Le lien de réinitialisation du mot de passe est invalide. Veuillez réessayer."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PasswordResetSerializer

    @swagger_auto_schema(request_body=PasswordResetSerializer)
    def put(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = request.user
            old_password = serializer.validated_data["old_password"]
            new_password1 = serializer.validated_data["new_password1"]
            new_password2 = serializer.validated_data["new_password2"]

            # Vérifier si l'ancien mot de passe est correct
            if not user.check_password(old_password):
                return Response(
                    {"message": "L'ancien mot de passe est incorrect."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Vérifier si les nouveaux mots de passe correspondent
            if new_password1 != new_password2:
                return Response(
                    {"message": "Les nouveaux mots de passe ne correspondent pas."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Mettre à jour le mot de passe
            user.set_password(new_password1)
            user.save()

            return Response(
                {"message": "Le mot de passe a été changé avec succès."},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
