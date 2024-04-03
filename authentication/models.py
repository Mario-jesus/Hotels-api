from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
import stripe, uuid

stripe.api_key = settings.STRIPE_SECRET_KEY

# Create your models here.
def path_to_avatar(instance, filename):
    return f"avatars/{filename}"


class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=150, unique=True)
    avatar = models.ImageField(upload_to=path_to_avatar, null=True, blank=True)
    is_customer = models.BooleanField(default=True)
    is_hotelier = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "password", "is_hotelier"]


class Customer(models.Model):
    user = models.OneToOneField(CustomUser, primary_key=True, on_delete=models.CASCADE, related_name="customers")


class Hotelier(models.Model):
    user = models.OneToOneField(CustomUser, primary_key=True, on_delete=models.CASCADE, related_name="hoteliers")
    connect_account = models.CharField(max_length=50, null=True, blank=True)


User = get_user_model()

@receiver(post_save, sender=User)
def set_hotelier_as_staff(sender, instance, created, **kwargs):
    if not created and getattr(instance, '_profile_created', False):
        return

    if instance.is_hotelier and not hasattr(instance, 'hoteliers'):
        instance.is_customer = False
        connect_account = create_connect_account(instance.id, instance.email)
        if connect_account is not None:
            Hotelier.objects.create(user=instance, connect_account=connect_account.id)
        else:
            Hotelier.objects.create(user=instance)
    elif instance.is_customer and not hasattr(instance, 'customers'):
        Customer.objects.create(user=instance)
        instance.is_hotelier = False
        instance.is_staff = False
        instance.is_superuser = False
        create_stripe_customer(instance.id, instance.email)

    instance._profile_created = True
    instance.save()


def create_stripe_customer(id, email):
    try:
        customer = stripe.Customer.create(
            id=id,
            email=email,
        )
    except stripe.error.StripeError as e:
        print(f"Error creating client in Stripe: {e}")
        return

    return customer


def get_or_create_customer(request_user) -> tuple[stripe.Customer, bool]:
    """
    customer, create = get_or_create_customer(request.user)
    """
    create = False
    user_id = str(request_user.customers.user_id)
    try:
        customer = stripe.Customer.retrieve(user_id)
    except stripe.error.InvalidRequestError:
        customer = create_stripe_customer(user_id, request_user.email)
        if customer:
            create = True
        else:
            raise ValueError(f"An error occurred while trying to create customer.")

    return customer, create


def create_connect_account(id: str, email: str, raise_errors=False):
    try:
        connect_account = stripe.Account.create(
            type="express",
            country="MX",
            email=email,
            metadata={"hotelier_id": id},
        )
    except Exception as err:
        if raise_errors:
            raise err
        return

    return connect_account


def get_or_create_connect_account(request_user) -> tuple[stripe.Account, bool]:
    """
    connect_account, create = get_or_create_connect_account(request.user)
    """
    create = False
    user_id = str(request_user.hoteliers.user_id)
    try:
        connect_account = request_user.hoteliers.connect_account
        if not connect_account:
            raise ValueError
    except ValueError:
        connect_account = create_connect_account(user_id, request_user.email, True)
        if connect_account:
            request_user.hoteliers.update(connect_account=connect_account).save()
            create = True
        else:
            raise ValueError(f"An error occurred while trying to create connect account.")

    return connect_account, create
