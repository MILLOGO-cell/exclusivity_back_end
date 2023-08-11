from rest_framework import serializers
from .models import (
    Post,
    SimplePost,
    EventPost,
    Comment,
    Like,
)
from accounts.serializers import UserSerializer
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model


class CommentSerializer(serializers.ModelSerializer):
    sub_comments = serializers.SerializerMethodField()
    user_details = UserSerializer(source="user", read_only=True)
    user = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all(),
        default=serializers.CurrentUserDefault(),
    )  # Fermez correctement le PrimaryKeyRelatedField ici
    comment_count = serializers.SerializerMethodField()
    likes_count = serializers.IntegerField(source="get_likes_count", read_only=True)
    liked_users = serializers.SerializerMethodField()
    is_liked_by_current_user = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "parent_comment",
            "user",
            "user_details",
            "content",
            "created_at",
            "content_type",
            "object_id",
            "sub_comments",
            "comment_count",
            "likes_count",
            "is_liked_by_current_user",
            "liked_users",
        ]

    # depth = 1  # Spécifier la profondeur de sérialisation (commentaires et sous-commentaires)

    def get_sub_comments(self, obj):
        # Récupérer les sous-commentaires du commentaire actuel (obj)
        sub_comments = Comment.objects.filter(parent_comment=obj)

        # Récursivement sérialiser les sous-commentaires avec le même serializer
        serializer = CommentSerializer(sub_comments, many=True)

        return serializer.data

    def get_comment_count(self, obj):
        return obj.sub_comments.count()

    def get_liked_users(self, obj):
        liked_users = obj.likes.values_list("user__username", flat=True)
        return list(liked_users)

    def get_is_liked_by_current_user(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.liked_users.filter(id=request.user.id).exists()
        return False

    # def to_representation(self, instance):
    #     # Personnaliser la représentation des données en fonction de la méthode de requête
    #     if self.context["request"].method == "GET":
    #         return super().to_representation(instance)
    #     else:
    #         # Retourner l'ID de l'auteur pour les requêtes POST
    #         ret = super().to_representation(instance)
    #         ret.pop("author")
    #         return ret


class PostSerializer(serializers.ModelSerializer):
    # Champs pour les requêtes GET
    author = serializers.StringRelatedField()
    author_get = UserSerializer(source="author", read_only=True)

    comments_count = serializers.IntegerField(
        source="get_comments_count", read_only=True
    )
    likes_count = serializers.IntegerField(source="get_likes_count", read_only=True)
    liked_users = serializers.SerializerMethodField()
    is_liked_by_current_user = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True, required=False)

    class Meta:
        model = Post
        fields = [
            "id",
            "content",
            "author",
            "author_get",  # Champ pour les requêtes GET
            "created_at",
            "media",
            "is_public",
            "comments_count",
            "likes_count",
            "is_liked_by_current_user",
            "liked_users",
            "comments",
        ]

    def get_liked_users(self, obj):
        liked_users = obj.likes.values_list("user__username", flat=True)
        return list(liked_users)

    def get_is_liked_by_current_user(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.liked_users.filter(id=request.user.id).exists()
        return False

    def to_representation(self, instance):
        # Personnaliser la représentation des données en fonction de la méthode de requête
        if self.context["request"].method == "GET":
            return super().to_representation(instance)
        else:
            # Retourner l'ID de l'auteur pour les requêtes POST
            ret = super().to_representation(instance)
            ret.pop("author")
            return ret


class SimplePostSerializer(PostSerializer):
    class Meta(PostSerializer.Meta):
        model = SimplePost
        fields = PostSerializer.Meta.fields + ["is_simple"]


class EventPostSerializer(PostSerializer):
    class Meta(PostSerializer.Meta):
        model = EventPost
        fields = PostSerializer.Meta.fields + [
            "title",
            "date",
            "time",
            "location",
            "is_event",
        ]


class LikeSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    content_type = serializers.PrimaryKeyRelatedField(
        queryset=ContentType.objects.all()
    )

    class Meta:
        model = Like
        fields = ["id", "user", "content_type", "object_id", "user_info"]
