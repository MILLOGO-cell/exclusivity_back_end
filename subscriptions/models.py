# from django.db import models
# from django.contrib.auth import get_user_model


# class Subscription(models.Model):
#     subscriber = models.ForeignKey(
#         get_user_model(), related_name="subscriptions", on_delete=models.CASCADE
#     )
#     creator = models.ForeignKey(
#         get_user_model(), related_name="subscribers", on_delete=models.CASCADE
#     )
#     Subscription_date = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"{self.subscriber.email} s'abonne à {self.creator.email}"

#     class Meta:
#         verbose_name = "Abonnement"  # Nom en français pour le modèle
#         verbose_name_plural = "Abonnements"
