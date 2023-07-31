from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import User


@receiver(post_save, sender=User)
def check_subscription_expiry(sender, instance, **kwargs):
    if instance.is_creator and instance.subscription_expiry is not None:
        if instance.subscription_expiry <= timezone.now():
            instance.is_active = False
            instance.save()
