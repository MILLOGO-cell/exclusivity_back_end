from django.db import models
from django.contrib.auth import get_user_model


class Feedback(models.Model):
    sender = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    recipient = models.ForeignKey(get_user_model(), related_name='received_feedbacks', on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"De: {self.sender.email}, À: {self.recipient.email}"
