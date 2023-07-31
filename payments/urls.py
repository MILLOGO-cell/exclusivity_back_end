from django.urls import path,include
from .views import PaymentViewSet
from rest_framework import routers

router = routers.DefaultRouter()
router.register('payments', PaymentViewSet)

 
urlpatterns = [
     path('', include(router.urls))
]