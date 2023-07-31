from django.urls import path,include
from .views import PostViewSet,LikeViewSet,CommentViewSet,SimplePostViewSet,EventPostViewSet
from rest_framework import routers

router = routers.DefaultRouter()
router.register('postes', PostViewSet)
router.register('likes', LikeViewSet)
router.register('comments', CommentViewSet)
router.register('simple-posts', SimplePostViewSet)
router.register('event_posts', EventPostViewSet)

 
urlpatterns = [
     path('', include(router.urls))
]