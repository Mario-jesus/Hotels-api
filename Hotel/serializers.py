from rest_framework import serializers
from administrator.serializers import ServicesSerializer, ImageCategorySerializer
from drf_extra_fields.fields import Base64ImageField
from .models import *


class ServicesHotelSerializer(serializers.ModelSerializer):

    class Meta:
        model = ServicesHotel
        fields = "__all__"


class ImageSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=True)

    class Meta:
        model = Image
        fields = "__all__"


class RoomTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = RoomType
        fields = "__all__"


class CoordinateSerializer(serializers.ModelSerializer):

    class Meta:
        model = LocationCoordinates
        fields = ('latitude', 'longitude')


class HotelSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=True)

    class Meta:
        model = Hotel
        fields = (
            'id',
            'hotelier',
            'name',
            'image',
            'description',
            'phone',
            'address',
            'city',
            'state',
            'rating',
            'coordinates',
            'services',
            'images',
            'room_types',
        )

    class NestedServicesHotelSerializer(serializers.ModelSerializer):
        service = ServicesSerializer(read_only=True)

        class Meta:
            model = ServicesHotel
            fields = ('id', 'price', 'description', 'service')

    class NestedImageSerializer(serializers.ModelSerializer):
        category = ImageCategorySerializer(read_only=True)

        class Meta:
            model = Image
            fields = ('id', 'image', 'description', 'category')

    coordinates = CoordinateSerializer()
    services = NestedServicesHotelSerializer(read_only=True, many=True)
    images = NestedImageSerializer(read_only=True, many=True)
    room_types = RoomTypeSerializer(read_only=True, many=True)

    def create(self, validated_data):
        coordinates_data = validated_data.pop("coordinates")
        hotel = Hotel.objects.create(**validated_data)
        LocationCoordinates.objects.create(hotel=hotel, **coordinates_data)
        return hotel
    
    def update(self, instance, validated_data):
        coordinates_data = validated_data.pop("coordinates", None)
        instance.name = validated_data.get("name", instance.name)
        instance.description = validated_data.get("description", instance.description)
        instance.phone = validated_data.get("phone", instance.phone)
        instance.address = validated_data.get("address", instance.address)
        instance.city = validated_data.get("city", instance.city)
        instance.state = validated_data.get("state", instance.state)
        instance.rating = validated_data.get("rating", instance.rating)
        instance.save()

        if coordinates_data:
            coordinate_instance = instance.coordinates
            coordinate_instance.latitude = coordinates_data.get("latitude", coordinate_instance.latitude)
            coordinate_instance.longitude = coordinates_data.get("longitude", coordinate_instance.longitude)

            coordinate_instance.save()

        return instance

    def partial_update(self, instance, validated_data):
        self.update(instance, validated_data)
