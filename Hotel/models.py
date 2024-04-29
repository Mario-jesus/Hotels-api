from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext as _
from authentication.models import Hotelier
from administrator.models import Services, ImageCategory
from decimal import Decimal
import uuid

# Create your models here.
class Hotel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hotelier = models.ForeignKey(Hotelier, on_delete=models.CASCADE, related_name="hotels", editable=False)
    name = models.CharField(max_length=100, verbose_name="Nombre del hotel")
    description = models.TextField(verbose_name="Descripción")
    phone = models.CharField(max_length=20, verbose_name='Teléfono')
    address = models.TextField(verbose_name="Dirección")
    city = models.CharField(max_length=50, verbose_name="Ciudad")
    state = models.CharField(max_length=50, verbose_name="Estado")
    rating = models.PositiveSmallIntegerField(validators=[MaxValueValidator(5)], verbose_name="Calificación")

    def check_room_availability(self, checkin: str, checkout: str) -> dict[list[dict]]:
        """
        check_room_availability("YYYY-MM-DD", "YYYY-MM-DD") -> {hotel_id: List[Room]}

        Devuelve una lista de habitaciones disponibles en el rango de fechas indicado por los parámetros.
        Si no hay habitación disponible para alguna fecha devuelve una lista vacía.
        """
        rts = self.room_types.all()
        room_availability = [rt.get_rooms_available(checkin, checkout) for rt in rts]
        return {"id": str(self.id), "name": self.name, "room_types": room_availability}

    class Meta:
        verbose_name = "Hotel"
        verbose_name_plural = "Hoteles"
        ordering = ["-rating", "name"]

    def  __str__(self):
        return str(self.name)


class LocationCoordinates(models.Model):
    hotel = models.OneToOneField(Hotel, on_delete=models.CASCADE, related_name="coordinates", editable=False)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, validators=[MinValueValidator(Decimal("-90")), MaxValueValidator(Decimal("90"))], verbose_name="Latitud")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, validators=[MinValueValidator(Decimal("-180")), MaxValueValidator(Decimal("180"))], verbose_name="Longitud")

    class Meta:
        verbose_name = "coordenadas de la ubicación"
        verbose_name_plural = "coordenadas de las ubicaciones"

    def __str__(self):
        return f'{self.latitude}, {self.longitude}'


class RoomType(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hotel = models.ForeignKey(
        Hotel, on_delete=models.CASCADE, related_name="room_types", editable=True
    )
    type = models.CharField(max_length=50, verbose_name="Tipo de habitación")
    capacity = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(20)], verbose_name="Capacidad de personas"
    )
    price = models.DecimalField(
        max_digits=8, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Precio por noche"
    )
    rooms = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(50)], verbose_name="Total de habitaciones"
    )
    description = models.TextField(null=True, blank=True, verbose_name="Descripción")

    def get_rooms_available(self, checkin: str, checkout: str) -> dict:
        """
        Devuelve el número total de habitaciones disponibles en una fecha determinada.
        El formato de entrada es un string con la forma 'YYYY-MM-DD'.
        """
        room_reservations = self.room_reservations.all()
        reservations = 0

        for room_reservation in room_reservations:
            reservation = room_reservation.customer_reservation
            if reservation.status == "RE":
                if (reservation.checkin <= checkin and reservation.checkout > checkin) or (reservation.checkin < checkout and reservation.checkout > checkout):
                    # Si hay alguna reserva activa (en curso) en las fechas dadas, se suma a las reservas totales
                    reservations += 1

        return {"id": str(self.id), "rooms_available": self.rooms - reservations, "type": self.type}

    class Meta:
        verbose_name = "Habitación"
        verbose_name_plural = "Habitaciones"

    def __str__(self):
        return str(self.type)


class ServicesHotel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service = models.ForeignKey(Services, on_delete=models.PROTECT, editable=True)
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='services', editable=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))], blank=True, null=True, verbose_name="Precio")
    description = models.TextField(blank=True, null=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Inclusión del servicio en el hotel"
        unique_together = ('service', 'hotel')

    def __str__(self):
        return f'{self.service} | {self.hotel}'


class Image(models.Model):

    def path_to_images(instance, filename):
        return f"images/{instance.hotel.id}/{filename}"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(ImageCategory, on_delete=models.PROTECT, verbose_name="Categorías")
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to=path_to_images, verbose_name="Imagen")
    description = models.TextField(verbose_name="Descripción", null=True, blank=True)

    class Meta:
        verbose_name = "Imagen"
        verbose_name_plural = "Imágenes"
