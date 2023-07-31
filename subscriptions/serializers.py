from rest_framework import serializers
from .models import Subscription


class SubscriptionSerializer(serializers.ModelSerializer):
    subscriber = serializers.StringRelatedField()
    creator = serializers.StringRelatedField()

    class Meta:
        model = Subscription
        fields = ["id", "subscriber", "creator"]
