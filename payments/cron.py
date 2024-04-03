from django.utils import timezone
from .models import Reservation

def verify_expiration_reservations():
    expired_reservations = Reservation.objects.filter(checkout__lt=timezone.now())

    for reservation in expired_reservations:
        room_reservations = reservation.bedrooms.all()

        for room_reservation in room_reservations:
            room_reservation.status = "EX"
            room_reservation.save(update_fields=['status'])

        reservation.status = "EX"
        reservation.save(update_fields=['status'])
