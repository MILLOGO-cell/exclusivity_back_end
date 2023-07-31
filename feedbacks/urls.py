from django.urls import path,include
from .views import FeedbackViewSet
from rest_framework import routers

router = routers.DefaultRouter()
router.register('feedback', FeedbackViewSet)

 
urlpatterns = [
     path('', include(router.urls))
]