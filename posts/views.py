from rest_framework import viewsets
from .models import Post, SimplePost, EventPost, Comment, Like
from .serializers import (
    PostSerializer,
    SimplePostSerializer,
    EventPostSerializer,
    CommentSerializer,
    LikeSerializer,
)
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .permissions import IsCreatorOrReadOnly, IsPublicPostOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from drf_yasg.utils import swagger_auto_schema


class SimplePostViewSet(viewsets.ModelViewSet):
    queryset = SimplePost.objects.all()
    # serializer_class = SimplePostSerializer
    permission_classes = [IsCreatorOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action == "comments":
            return CommentSerializer

        # Check if the 'date' field is present in request data to determine the serializer
        is_event_post = self.request.data.get("location") is not None

        if is_event_post:
            return EventPostSerializer
        else:
            return SimplePostSerializer

    @action(detail=True, methods=["get"])
    def comments(self, request, pk=None):
        post = self.get_object()

        # Sérialiser le post avec les commentaires inclus
        serializer = PostSerializer(post)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EventPostViewSet(viewsets.ModelViewSet):
    queryset = EventPost.objects.select_related("author")
    serializer_class = EventPostSerializer
    permission_classes = [IsCreatorOrReadOnly]

    def perform_create(self, serializer):
        # Assurez-vous que l'auteur du post est l'utilisateur actuellement connecté
        serializer.save(author=self.request.user)

    @action(detail=True, methods=["get"])
    def comments(self, request, pk=None):
        post = self.get_object()

        # Sérialiser le post avec les commentaires inclus
        serializer = EventPostSerializer(post)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    # serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action == "comments":
            return CommentSerializer

        # Check if the 'date' field is present in request data to determine the serializer
        is_event_post = self.request.data.get("location") is not None

        if is_event_post:
            return EventPostSerializer
        else:
            return SimplePostSerializer

    def perform_create(self, serializer):
        date = self.request.data.get("date")
        time = self.request.data.get("time")
        location = self.request.data.get("location")

        # Créer un nouvel objet Post en fonction des données du serializer
        post = serializer.save()

        # Si c'est un EventPost, mettez à jour les champs spécifiques
        if isinstance(post, EventPost):
            post.date = date
            post.time = time
            post.location = location
            post.save()

    @action(detail=True, methods=["get"])
    def comments(self, request, pk=None):
        post = self.get_object()

        # Sérialiser le post avec les commentaires inclus
        serializer = PostSerializer(post)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CommentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, post_id):
        # Récupérer le post associé à l'ID donné
        post = get_object_or_404(Post, id=post_id)

        # Récupérer les commentaires directs liés au post
        comments = Comment.objects.filter(
            content_type__model="post", object_id=post_id, parent_comment=None
        )

        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=CommentSerializer)
    def post(self, request, post_id):
        # Créer un nouveau commentaire sur le post
        content_type = ContentType.objects.get_for_model(Post)
        content = request.data.get("content")
        parent_comment_id = request.data.get("parent_comment_id")
        data = {
            "content_type": content_type.pk,
            "object_id": post_id,
            "user": request.user.id,
            "parent_comment": None,  # Pas de commentaire parent pour un nouveau commentaire sur le post
            "content": content,
        }
        if parent_comment_id:
            # Si parent_comment_id est présent, définir la relation avec le commentaire parent
            data["parent_comment"] = parent_comment_id

        serializer = CommentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            # Appeler la méthode pour mettre à jour le nombre de réponses du commentaire parent
            if parent_comment_id:
                self.update_comment_count(parent_comment_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update_comment_count(self, comment_id):
        # Récupérer le commentaire parent
        parent_comment = get_object_or_404(Comment, id=comment_id)

        # Compter le nombre de sous-commentaires liés au commentaire parent
        comment_count = Comment.objects.filter(parent_comment=parent_comment).count()

        # Mettre à jour le champ comment_count du commentaire parent avec le nombre de réponses
        parent_comment.comment_count = comment_count
        parent_comment.save()


class CommentSimpleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, post_id):
        # Récupérer le post associé à l'ID donné
        post = get_object_or_404(SimplePost, id=post_id)

        # Récupérer les commentaires directs liés au post
        comments = Comment.objects.filter(
            content_type__model="simplepost", object_id=post_id, parent_comment=None
        )

        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=CommentSerializer)
    def post(self, request, post_id):
        # Créer un nouveau commentaire sur le post
        content_type = ContentType.objects.get_for_model(SimplePost)
        content = request.data.get("content")
        parent_comment_id = request.data.get("parent_comment_id")
        data = {
            "content_type": content_type.pk,
            "object_id": post_id,
            "user": request.user.id,
            "parent_comment": None,  # Pas de commentaire parent pour un nouveau commentaire sur le post
            "content": content,
        }
        if parent_comment_id:
            # Si parent_comment_id est présent, définir la relation avec le commentaire parent
            data["parent_comment"] = parent_comment_id

        serializer = CommentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            # Appeler la méthode pour mettre à jour le nombre de réponses du commentaire parent
            if parent_comment_id:
                self.update_comment_count(parent_comment_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update_comment_count(self, comment_id):
        # Récupérer le commentaire parent
        parent_comment = get_object_or_404(Comment, id=comment_id)

        # Compter le nombre de sous-commentaires liés au commentaire parent
        comment_count = Comment.objects.filter(parent_comment=parent_comment).count()

        # Mettre à jour le champ comment_count du commentaire parent avec le nombre de réponses
        parent_comment.comment_count = comment_count
        parent_comment.save()


class CommentEventAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, post_id):
        # Récupérer le post associé à l'ID donné
        post = get_object_or_404(EventPost, id=post_id)

        # Récupérer les commentaires directs liés au post
        comments = Comment.objects.filter(
            content_type__model="eventpost", object_id=post_id, parent_comment=None
        )

        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(request_body=CommentSerializer)
    def post(self, request, post_id):
        # Créer un nouveau commentaire sur le post
        content_type = ContentType.objects.get_for_model(EventPost)
        content = request.data.get("content")
        parent_comment_id = request.data.get("parent_comment_id")
        data = {
            "content_type": content_type.pk,
            "object_id": post_id,
            "user": request.user.id,
            "parent_comment": None,  # Pas de commentaire parent pour un nouveau commentaire sur le post
            "content": content,
        }
        if parent_comment_id:
            # Si parent_comment_id est présent, définir la relation avec le commentaire parent
            data["parent_comment"] = parent_comment_id

        serializer = CommentSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            # Appeler la méthode pour mettre à jour le nombre de réponses du commentaire parent
            if parent_comment_id:
                self.update_comment_count(parent_comment_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update_comment_count(self, comment_id):
        # Récupérer le commentaire parent
        parent_comment = get_object_or_404(Comment, id=comment_id)

        # Compter le nombre de sous-commentaires liés au commentaire parent
        comment_count = Comment.objects.filter(parent_comment=parent_comment).count()

        # Mettre à jour le champ comment_count du commentaire parent avec le nombre de réponses
        parent_comment.comment_count = comment_count
        parent_comment.save()


class LikeView(APIView):
    permission_classes = [IsAuthenticated]

    def get_post(self, post_id):
        try:
            return Post.objects.get(pk=post_id)
        except Post.DoesNotExist:
            return None

    def get_like(self, user, post):
        try:
            return Like.objects.get(
                user=user,
                content_type=ContentType.objects.get_for_model(post),
                object_id=post.id,
            )
        except Like.DoesNotExist:
            return None

    def get(self, request, post_id):
        post = self.get_post(post_id)
        if post is None:
            return Response(
                {"detail": "Post not found."}, status=status.HTTP_404_NOT_FOUND
            )

        likes = Like.objects.filter(
            content_type=ContentType.objects.get_for_model(post), object_id=post.id
        )
        serializer = LikeSerializer(likes, many=True)
        return Response(serializer.data)

    def post(self, request, post_id):
        post = self.get_post(post_id)
        if post is None:
            return Response(
                {"detail": "Post not found."}, status=status.HTTP_404_NOT_FOUND
            )

        like = self.get_like(request.user, post)
        if like:
            like.delete()
            post.liked_users.remove(request.user)
            return Response({"status": "disliked"})
        else:
            like = Like(
                user=request.user,
                content_type=ContentType.objects.get_for_model(post),
                object_id=post.id,
            )
            like.user_info = {
                "username": request.user.username,
                "email": request.user.email,
            }
            like.save()
            post.liked_users.add(request.user)
            return Response({"status": "liked", "user_info": like.user_info})


class SimplePostLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def get_post(self, post_id):
        try:
            return SimplePost.objects.get(pk=post_id)
        except SimplePost.DoesNotExist:
            return None

    def get_like(self, user, post):
        try:
            return Like.objects.get(
                user=user,
                content_type=ContentType.objects.get_for_model(post),
                object_id=post.id,
            )
        except Like.DoesNotExist:
            return None

    def get(self, request, post_id):
        post = self.get_post(post_id)
        if post is None:
            return Response(
                {"detail": "Post not found."}, status=status.HTTP_404_NOT_FOUND
            )

        likes = Like.objects.filter(
            content_type=ContentType.objects.get_for_model(post), object_id=post.id
        )
        serializer = LikeSerializer(likes, many=True)
        return Response(serializer.data)

    def post(self, request, post_id):
        post = self.get_post(post_id)
        if post is None:
            return Response(
                {"detail": "Post not found."}, status=status.HTTP_404_NOT_FOUND
            )

        like = self.get_like(request.user, post)
        if like:
            like.delete()
            post.liked_users.remove(request.user)
            return Response({"status": "disliked"})
        else:
            like = Like(
                user=request.user,
                content_type=ContentType.objects.get_for_model(post),
                object_id=post.id,
            )
            like.user_info = {
                "username": request.user.username,
                "email": request.user.email,
            }
            like.save()
            post.liked_users.add(request.user)
            return Response({"status": "liked", "user_info": like.user_info})


class EventPostLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, post_id):
        event_post = get_object_or_404(EventPost, id=post_id)

        like, created = Like.objects.get_or_create(
            user=request.user,
            content_type=ContentType.objects.get_for_model(event_post),
            object_id=event_post.id,
        )

        if not created:
            like.delete()
            event_post.liked_users.remove(request.user)

        return Response({"status": "liked" if created else "disliked"})

    def get(self, request, post_id):
        event_post = get_object_or_404(EventPost, id=post_id)
        likes = Like.objects.filter(
            content_type=ContentType.objects.get_for_model(event_post),
            object_id=event_post.id,
        )
        serializer = LikeSerializer(likes, many=True)
        return Response(serializer.data)


class CommentLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def get_comment(self, comment_id):
        try:
            return Comment.objects.get(pk=comment_id)
        except Comment.DoesNotExist:
            return None

    def get_like(self, user, comment):
        try:
            return Like.objects.get(
                user=user,
                content_type=ContentType.objects.get_for_model(comment),
                object_id=comment.id,
            )
        except Like.DoesNotExist:
            return None

    def get(self, request, comment_id):
        comment = self.get_comment(comment_id)
        if comment is None:
            return Response(
                {"detail": "comment not found."}, status=status.HTTP_404_NOT_FOUND
            )

        likes = Like.objects.filter(
            content_type=ContentType.objects.get_for_model(comment),
            object_id=comment.id,
        )
        serializer = LikeSerializer(likes, many=True)
        return Response(serializer.data)

    def post(self, request, comment_id):
        comment = self.get_comment(comment_id)
        if comment is None:
            return Response(
                {"detail": "Post not found."}, status=status.HTTP_404_NOT_FOUND
            )

        like = self.get_like(request.user, comment)
        if like:
            like.delete()
            comment.liked_users.remove(request.user)
            return Response({"status": "disliked"})
        else:
            like = Like(
                user=request.user,
                content_type=ContentType.objects.get_for_model(comment),
                object_id=comment.id,
            )
            like.user_info = {
                "username": request.user.username,
                "email": request.user.email,
            }
            like.save()
            comment.liked_users.add(request.user)
            return Response({"status": "liked", "user_info": like.user_info})
