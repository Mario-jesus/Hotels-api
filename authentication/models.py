from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
def path_to_avatar(instance, filename):
    return f"avatars/{filename}"


class CustomUser(AbstractUser):
    email = models.EmailField(max_length=150, unique=True)
    avatar = models.ImageField(upload_to=path_to_avatar, null=True, blank=True)
    is_customer = models.BooleanField(default=True)
    is_hotelier = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "password", "is_hotelier"]


class Customer(models.Model):
    user = models.OneToOneField(CustomUser, primary_key=True, on_delete=models.CASCADE)


class Hotelier(models.Model):
    user = models.OneToOneField(CustomUser, primary_key=True, on_delete=models.CASCADE)


User = get_user_model()

@receiver(post_save, sender=User)
def set_hotelier_as_staff(sender, instance, created, **kwargs):
    if not created and getattr(instance, '_profile_created', False):
        return

    if instance.is_hotelier and not hasattr(instance, 'hotelier'):
        Hotelier.objects.create(user=instance)
        instance.is_staff = True
        instance.is_customer = False
        instance.is_hotelier = True
    elif instance.is_customer and not hasattr(instance, 'customer'):
        Customer.objects.create(user=instance)
        instance.is_hotelier = False
        instance.is_staff = False
        instance.is_superuser = False

    instance._profile_created = True
    instance.save()
