from django.core.mail import send_mail
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from .models import User, Subscription
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
from .serializers import (
    UserSerializer,
    UserPhotoUpdateSerializer,
    SubscriptionSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from random import randint
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import api_view, permission_classes
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.decorators import action
from rest_framework import status, viewsets
from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import ListAPIView
from rest_framework import filters
from django.shortcuts import render


class UserSearchView(ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["username", "email", "first_name", "last_name"]


class UserListView(APIView):
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_image_url(request, id):
    user = get_object_or_404(User, id=id)
    image_url = settings.MEDIA_URL + str(user.image) if user.image else None
    return JsonResponse({"image_url": image_url})


class UserDetails(APIView):
    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Récupérer l'utilisateur connecté
        user = request.user

        # Serializer l'utilisateur pour renvoyer les détails au frontend
        user_serializer = UserSerializer(user)

        # Récupérer les IDs des créateurs auxquels l'utilisateur s'est abonné
        subscribed_creator_ids = []
        if not user.is_creator:
            subscribed_creator_ids = user.get_subscribed_creators_ids()

        # Ajouter les IDs des créateurs abonnés aux détails de l'utilisateur
        user_serializer.data["subscribed_creators_ids"] = subscribed_creator_ids

        response_data = {
            "user_details": user_serializer.data,
        }

        return Response(response_data)


class UpdateUserPhotoView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        # Récupérer l'utilisateur connecté
        user = request.user
        # Récupérer l'image téléchargée depuis la requête
        image = request.FILES.get("image")
        # Mettre à jour le champ 'image' de l'utilisateur avec la nouvelle image
        user.image = image
        user.save()
        # Serializer l'utilisateur pour renvoyer les données au frontend
        serializer = UserPhotoUpdateSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpdateUserView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request):
        # Récupérer l'utilisateur connecté
        user = request.user
        # Serializer l'utilisateur pour renvoyer les données au frontend
        serializer = UserSerializer(user)
        return Response(serializer.data)

    @swagger_auto_schema(request_body=UserSerializer)
    def put(self, request):
        # Récupérer l'utilisateur connecté
        user = request.user
        # Serializer l'utilisateur avec les données reçues du frontend
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid():
            # Sauvegarder les modifications de l'utilisateur
            serializer.save()
            # Répéter la sérialisation pour inclure tous les champs de l'utilisateur
            updated_user = self.serializer_class(user)
            return Response(updated_user.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    @method_decorator(login_required)
    def put(self, request):
        # Récupérer l'utilisateur connecté
        user = request.user
        current_password = request.data.get("current_password", None)
        new_password = request.data.get("new_password", None)
        # Vérifier que le mot de passe actuel correspond à celui de l'utilisateur
        if not user.check_password(current_password):
            return Response(
                {"error": "Le mot de passe actuel est incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Mettre à jour le mot de passe de l'utilisateur avec le nouveau mot de passe
        user.set_password(new_password)
        user.save()
        # Garder la session d'authentification active en mettant à jour le hachage de session
        update_session_auth_hash(request, user)
        return Response(
            {"message": "Le mot de passe a été modifié avec succès."},
            status=status.HTTP_200_OK,
        )


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
                activation_link = f"{current_site}/api/utilisateurs/verification-email/{user.pk}/{activation_token}"
                send_activation_email(
                    user.username, email, activation_link
                )  # Fonction pour envoyer l'e-mail

                return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    serializer_class = LoginSerializer

    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data.get("username")
        password = serializer.validated_data.get("password")

        # Vérifier les informations d'identification de l'utilisateur
        user = authenticate(request, username=username, password=password)
        if not user:
            return Response(
                {"error": "Nom d'utilisateur ou mot de passe incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.is_verified:
            return Response(
                {
                    "error": "Votre compte n'est pas encore activé. Veuillez vérifier votre boîte e-mail pour activer votre compte."
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        # Sérialiser l'utilisateur avec les champs followers_count et subscriptions_count
        user_serializer = UserSerializer(user)
        serialized_user = user_serializer.data

        # Ajouter les champs followers_count et subscriptions_count aux données sérialisées
        serialized_user["followers_count"] = user.get_followers_count()
        serialized_user["subscriptions_count"] = user.get_subscriptions_count()
        # Générer les tokens JWT
        refresh = RefreshToken.for_user(user)
        tokens = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            # "user": {
            #     "id": user.id,
            #     "username": user.username,
            #     "email": user.email,
            #     "is_creator": user.is_creator,
            #     "is_verified": user.is_verified,
            #     "followers_count": user.followers_count,
            #     "subscriptions_count": user.subscriptions_count,
            # },
            "user": serialized_user,
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
            user.is_verified = True
            user.save()
            template = "accounts/activation_result.html"
            message = "Votre compte a été activé avec succès."
            # return Response(
            #     {"message": "Votre compte a été activé avec succès."},
            #     status=status.HTTP_200_OK,
            # )
        else:
            template = "accounts/activation_result.html"
            message = "Le lien d'activation est invalide ou a expiré. Veuillez réessayer ou contacter le support."
            # return Response(
            #     {"message": "Le lien d'activation est invalide."},
            #     status=status.HTTP_400_BAD_REQUEST,
            # )
        return render(request, template, {"message": message})


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
            # Generate verification code (e.g., a 6-digit code)
            verification_code = str(randint(100000, 999999))

            # Save the verification code in the user's profile or as a separate model if needed
            user.verification_code = verification_code
            user.verification_code_expiration = timezone.now() + timedelta(minutes=30)
            user.save()

            # Send the verification code to user's email
            subject = "Demande de changement de mot de passe"
            message = f"Bonjour {user.username},\n\nVotre code de vérification pour réinitialiser votre mot de passe est : {verification_code}\n\nSi vous n'avez pas effectué cette demande, veuillez ignorer cet e-mail.\n\nMerci,\nL'équipe Exclusivity"
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

        return Response(
            {
                "message": "Si cette adresse e-mail est valide, vous recevrez un e-mail contenant un code de vérification pour réinitialiser votre mot de passe."
            },
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    serializer_class = PasswordResetSerializer

    @swagger_auto_schema(request_body=PasswordResetSerializer)
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            verification_code = serializer.validated_data.get("verification_code")

            try:
                user = User.objects.get(verification_code=verification_code)
            except User.DoesNotExist:
                user = None

            if user and user.verification_code == verification_code:
                # Vérifier si le code de vérification n'a pas expiré
                expiration_time = user.verification_code_expiration
                if expiration_time and expiration_time >= datetime.now():
                    new_password = serializer.validated_data["new_password1"]
                    user.set_password(new_password)
                    user.save()
                    return Response(
                        {
                            "message": "Votre mot de passe a été réinitialisé avec succès."
                        },
                        status=status.HTTP_200_OK,
                    )
                else:
                    return Response(
                        {
                            "message": "Le code de vérification a expiré. Veuillez réessayer."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:
                return Response(
                    {
                        "message": "Le code de vérification est invalide. Veuillez réessayer."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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


class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["POST"])
    def subscribe(self, request):
        creator_id = request.data.get("creator")

        if creator_id is None:
            return Response(
                {"error": "ID du créateur manquant dans les données de la requête."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            creator = get_user_model().objects.get(id=creator_id)

        except get_user_model().DoesNotExist:
            return Response(
                {"error": "ID du créateur invalide."}, status=status.HTTP_404_NOT_FOUND
            )

        # Vérifier si l'utilisateur est déjà abonné au créateur
        if Subscription.objects.filter(
            subscriber=request.user, creator=creator
        ).exists():
            return Response({"message": "Déjà abonné."}, status=status.HTTP_200_OK)

        # Créer une instance d'abonnement
        Subscription.objects.create(subscriber=request.user, creator=creator)

        return Response(
            {"message": "Abonnement réussi."}, status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=["POST"])
    def unsubscribe(self, request):
        creator_id = request.data.get("creator")
        if creator_id is None:
            return Response(
                {"error": "ID du créateur manquant dans les données de la requête."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # creator = get_user_model().objects.get(id=creator_id, is_creator=True)
            creator = get_user_model().objects.get(
                id=creator_id,
            )
        except get_user_model().DoesNotExist:
            return Response(
                {"error": "ID du créateur invalide."}, status=status.HTTP_404_NOT_FOUND
            )

        # Vérifier si l'utilisateur est déjà abonné au créateur
        try:
            subscription = Subscription.objects.get(
                subscriber=request.user, creator=creator
            )
        except Subscription.DoesNotExist:
            return Response(
                {"message": "Pas d'abonnement trouvé."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Supprimer l'abonnement
        subscription.delete()

        return Response({"message": "Désabonnement réussi."}, status=status.HTTP_200_OK)
