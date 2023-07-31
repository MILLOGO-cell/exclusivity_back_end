from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet
from .models import Subscription
from .serializers import SubscriptionSerializer
from django.contrib.auth import get_user_model


class SubscriptionViewSet(ReadOnlyModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["POST"])
    def subscribe(self, request):
        creator_id = request.data.get("creator_id")
        if creator_id is None:
            return Response(
                {"erreur": "ID du créateur manquant dans les données de la requête."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            creator = get_user_model().objects.get(id=creator_id, is_creator=True)
        except get_user_model().DoesNotExist:
            return Response(
                {"erreur": "ID du créateur invalide."}, status=status.HTTP_404_NOT_FOUND
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
        creator_id = request.data.get("creator_id")
        if creator_id is None:
            return Response(
                {"erreur": "ID du créateur manquant dans les données de la requête."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            creator = get_user_model().objects.get(id=creator_id, is_creator=True)
        except get_user_model().DoesNotExist:
            return Response(
                {"erreur": "ID du créateur invalide."}, status=status.HTTP_404_NOT_FOUND
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
