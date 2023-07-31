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


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsCreatorOrReadOnly | IsPublicPostOrReadOnly]


class SimplePostViewSet(viewsets.ModelViewSet):
    queryset = SimplePost.objects.all()
    serializer_class = SimplePostSerializer
    permission_classes = [IsCreatorOrReadOnly]


class EventPostViewSet(viewsets.ModelViewSet):
    queryset = EventPost.objects.all()
    serializer_class = EventPostSerializer
    permission_classes = [IsCreatorOrReadOnly]


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class LikeViewSet(viewsets.ModelViewSet):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
