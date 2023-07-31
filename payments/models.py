from django.db import models
from django.contrib.auth import get_user_model


class Payment(models.Model):
    payer = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    # Ajoutez d'autres champs liés au paiement si nécessaire

    def __str__(self):
        return f"Paiement de {self.amount} € par {self.payer.email}"
