from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from authentication.models import Customer
from Hotel.models import Hotel, RoomType
from decimal import Decimal
import uuid

# Create your models here.
class Reservation(models.Model):
    RESERVATION_STATUS = (
        ('RE', _('Reserved')),
        ('EX', _('Expired')),
        ('CA', _('Cancelled')),
        ('RF', _('Refunded')),
        ('FA', _('Failed')),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hotel = models.ForeignKey(Hotel, on_delete=models.SET_NULL, null=True, related_name="reservations", verbose_name="Hotel")
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name="reservations", verbose_name="Cliente")
    name = models.CharField(max_length=40, verbose_name="Nombre")
    email = models.EmailField(max_length=150, verbose_name="Correo")
    phone = models.CharField(max_length=20, verbose_name="Teléfono")
    checkin = models.DateField(verbose_name="Fecha de llegada")
    checkout = models.DateField(verbose_name="Fecha de salida")
    status = models.CharField(max_length=2, choices=RESERVATION_STATUS, default='FA', editable=False)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))], null=True, editable=False)
    payment_intent = models.CharField(max_length=50, null=True, verbose_name="Intento de pago", editable=False)
    create_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el", editable=False)

    def clean(self, *args, **kwargs):
        super(Reservation, self).clean(*args, **kwargs)
        if self.checkout and self.checkin > self.checkout:
            raise ValidationError({'checkin': _('The arrival date must be before the departure date.')})

    class Meta:
        verbose_name = "Reservación"
        verbose_name_plural = "Reservaciones"
        ordering = ["-create_at"]


class RoomReservation(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_reservation = models.ForeignKey(
        Reservation, on_delete=models.SET_NULL, null=True, related_name="bedrooms", verbose_name="Reservación"
    )
    room_type = models.ForeignKey(
        RoomType, on_delete=models.SET_NULL, null=True, related_name="room_reservations", verbose_name="Tipo de Habitación"
    )
    rooms = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(50)],
        verbose_name="Total de habitaciones"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creado el", editable=False)

    class Meta:
        verbose_name = "Reserva de habitación"
        verbose_name_plural = "Reservas de habitación"
