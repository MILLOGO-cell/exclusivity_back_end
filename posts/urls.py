from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PostViewSet,
    CommentAPIView,
    CommentEventAPIView,
    CommentSimpleAPIView,
    SimplePostViewSet,
    EventPostViewSet,
    LikeView,
    SimplePostLikeView,
    EventPostLikeView,
    CommentLikeView,
)

router = DefaultRouter()
router.register("postes", PostViewSet)
# router.register("comments", CommentViewSet)
router.register("simple-posts", SimplePostViewSet)
router.register("event_posts", EventPostViewSet)
urlpatterns = [
    path("", include(router.urls)),
    path("postes/<int:post_id>/likes/", LikeView.as_view(), name="post-like"),
    path(
        "posts/<int:post_id>/comments/", CommentAPIView.as_view(), name="posts-comments"
    ),
    path(
        "simpleposts/<int:post_id>/comments/",
        CommentSimpleAPIView.as_view(),
        name="posts-comments",
    ),
    path(
        "eventposts/<int:post_id>/comments/",
        CommentEventAPIView.as_view(),
        name="posts-comments",
    ),
    path(
        "postes/simple/<int:post_id>/likes/",
        SimplePostLikeView.as_view(),
        name="simple-post-like",
    ),
    path(
        "postes/event/<int:post_id>/likes/",
        EventPostLikeView.as_view(),
        name="event-post-like",
    ),
    path(
        "postes/comment/<int:comment_id>/likes/",
        CommentLikeView.as_view(),
        name="comment-post-like",
    ),
]
