from rest_framework import serializers
from .models import *
from Hotel.models import Hotel, RoomType


class ReservationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Reservation
        fields = (
            'id',
            'hotel',
            'customer',
            'name',
            'email',
            'phone',
            'checkin',
            'checkout',
            'bedrooms',
        )

    class NestedRoomReservationSerializer(serializers.ModelSerializer):

        class Meta:
            model = RoomReservation
            fields = (
                "room_type",
                "rooms",
            )

    bedrooms = NestedRoomReservationSerializer(many=True)

    def create(self, validated_data):
        bedrooms_data = validated_data.pop("bedrooms")
        reservation = Reservation.objects.create(**validated_data)
        for room_item in bedrooms_data:
            RoomReservation.objects.create(customer_reservation=reservation, **room_item)

        return reservation

    def update(self, instance, validated_data):
        bedrooms_data = validated_data.pop("bedrooms", None)
        instance.hotel = validated_data.get("name", instance.name)
        instance.customer = validated_data.get("description", instance.description)
        instance.name = validated_data.get("phone", instance.phone)
        instance.email = validated_data.get("address", instance.address)
        instance.phone = validated_data.get("city", instance.city)
        instance.checkin = validated_data.get("state", instance.state)
        instance.checkout = validated_data.get("rating", instance.rating)

        for room_item_data in bedrooms_data:
            room_item = instance.bedrooms.get(id=room_item_data.get("id"))
            if room_item:
                room_item.room_type = room_item_data.get("room_type", room_item.room_type)
                room_item.rooms = room_item_data.get("rooms", room_item.rooms)
                room_item.save()
            else:
                RoomReservation.objects.create(customer_reservation=instance, **room_item_data)

        instance.save()
        return instance


class ReservationReadOnlySerializer(serializers.ModelSerializer):

    class Meta:
        model = Reservation
        fields = "__all__"

    class NestedRoomReservationSerializer(serializers.ModelSerializer):

        class Meta:
            model = RoomReservation
            fields = "__all__"

        class NestedRoomType(serializers.ModelSerializer):

            class Meta:
                model = RoomType
                fields = ("id", "type")

        room_type = NestedRoomType()

    class NestedHotelserializer(serializers.ModelSerializer):

        class Meta:
            model = Hotel
            fields = ("id", "name", "image")

    bedrooms = NestedRoomReservationSerializer(many=True)
    hotel = NestedHotelserializer()
