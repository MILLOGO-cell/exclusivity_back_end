# permissions.py

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsCreatorOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        # Les utilisateurs connectés peuvent commenter et liker
        if request.method in ("GET", "POST", "HEAD", "OPTIONS"):
            return True

        # Vérifier si l'utilisateur a le droit is_creator=True pour faire des publications
        return request.user.is_authenticated and request.user.is_creator


class IsPublicPostOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        # Autoriser les méthodes de lecture (GET, HEAD, OPTIONS) pour les utilisateurs non connectés
        if request.method in SAFE_METHODS and not request.user.is_authenticated:
            return True

        # Autoriser toutes les méthodes pour les utilisateurs connectés
        return request.user.is_authenticated
