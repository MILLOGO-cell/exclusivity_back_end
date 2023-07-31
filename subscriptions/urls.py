from django.urls import path, include
from .views import SubscriptionViewSet
from rest_framework import routers

router = routers.DefaultRouter()
router.register("abonnement", SubscriptionViewSet)


urlpatterns = [path("", include(router.urls))]
