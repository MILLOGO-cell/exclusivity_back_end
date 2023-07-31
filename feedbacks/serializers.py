from rest_framework import serializers, viewsets
from .models import Feedback

class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['id', 'sender', 'recipient', 'message', 'created_at']