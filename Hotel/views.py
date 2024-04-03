from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext as _
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from authentication.models import Hotelier
from .serializers import *
from .models import *

# Create your views here.
class IsHotelier(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_authenticated:
            return request.user and (request.user.is_staff or request.user.is_hotelier)
        else:
            return False


def capture_validation_error(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as err:
            try:
                return Response({"detail": err.messages[0]}, status=status.HTTP_400_BAD_REQUEST)
            except Exception :
                if isinstance(err.args, tuple):
                    if isinstance(err.args[0], dict):
                        return Response(dict(err.args[0]), status=status.HTTP_400_BAD_REQUEST)
                    return Response(str(err.args[0]), status=status.HTTP_400_BAD_REQUEST)
                return Response(str(err), status=status.HTTP_400_BAD_REQUEST)
    return wrapper


def validate_hotelier(data=None, is_destroy=False):
    def decorator(func):
        def wrapper(self, obj, *args, **kwargs):
            hotelier_id = self.request.user.hoteliers.user_id
            hotel_id = obj.hotel_id if is_destroy else self.request.data.get("hotel")
            try:
                hotel = Hotel.objects.get(id=hotel_id)
                kwargs["hotel"] = hotel
                if data and is_destroy:
                    Model, id_name, id_value = data.get("model_name"), data.get("id_name"), data.get("id_value")
                    eval(f"Model.objects.get(hotel=hotel, {id_name}=obj.{id_value})")
                elif data:
                    field_name, Model, id_value = data.get("field_name"), data.get("model_name"), data.get("id_value")
                    kwargs[field_name] = Model.objects.get(id=self.request.data.get(id_value))
            except ObjectDoesNotExist:
                raise ValidationError(_("The requested data is invalid or non-existent."))
            else:
                if not hotel.hotelier_id == hotelier_id:
                    raise PermissionDenied(_("You do not have the appropriate permissions to access this resource."))
            return func(self, obj, *args, **kwargs)
        return wrapper
    return decorator


class HotelViewSet(viewsets.ModelViewSet):
    queryset = Hotel.objects.all()
    serializer_class = HotelSerializer
    permission_classes = (IsHotelier,)

    def get_queryset(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_hotelier:
                return Hotel.objects.filter(hotelier_id=self.request.user.hoteliers.user_id)
        return super().get_queryset()

    def perform_create(self, serializer):
        hotelier_id = self.request.user.id
        serializer.save(hotelier=Hotelier.objects.get(user_id=hotelier_id))


class CoordinateViewSet(viewsets.ModelViewSet):
    queryset = LocationCoordinates.objects.all()
    serializer_class = CoordinateSerializer
    permission_classes = (IsHotelier,)


class ServicesHotelViewSet(viewsets.ModelViewSet):
    queryset = ServicesHotel.objects.select_related("service", "hotel")
    serializer_class = ServicesHotelSerializer
    permission_classes = (IsHotelier,)

    def get_queryset(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_hotelier:
                hotels = Hotel.objects.filter(hotelier=self.request.user.hoteliers.user_id)
                return ServicesHotel.objects.filter(hotel__in=hotels)
        return super().get_queryset()

    @capture_validation_error
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @validate_hotelier(data={"field_name": "service", "model_name": Services, "id_value": "service"})
    def perform_create(self, serializer, **kwargs):
        current_hotel = kwargs.get("hotel")
        current_service = kwargs.get("service")
        serializer.save(hotel=current_hotel, service=current_service)

    @capture_validation_error
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @validate_hotelier(data={"field_name": "service", "model_name": Services, "id_value": "service"})
    def perform_update(self, serializer, **kwargs):
        current_hotel = kwargs.get("hotel")
        current_service = kwargs.get("service")
        serializer.save(hotel=current_hotel, service=current_service)

    @validate_hotelier(data={"model_name": ServicesHotel, "id_name": "service", "id_value": "service_id"}, is_destroy=True)
    def perform_destroy(self, instance, **kwargs):
        super().perform_destroy(instance)


class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.select_related("hotel", "category")
    serializer_class = ImageSerializer
    permission_classes = (IsHotelier,)

    def get_queryset(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_hotelier:
                hotels = Hotel.objects.filter(hotelier=self.request.user.hoteliers.user_id)
                return Image.objects.filter(hotel__in=hotels)
        return super().get_queryset()

    @capture_validation_error
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @validate_hotelier(data={"field_name": "image_category", "model_name": ImageCategory, "id_value": "category"})
    def perform_create(self, serializer, **kwargs):
        current_hotel = kwargs.get("hotel")
        current_image_category = kwargs.get("image_category")
        serializer.save(hotel=current_hotel, category=current_image_category)

    @capture_validation_error
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @validate_hotelier(data={"field_name": "image_category", "model_name": ImageCategory, "id_value": "category"})
    def perform_update(self, serializer, **kwargs):
        current_hotel = kwargs.get("hotel")
        current_image_category = kwargs.get("image_category")
        serializer.save(hotel=current_hotel, category=current_image_category)

    @validate_hotelier(data={"model_name": Image, "id_name": "id", "id_value": "id"}, is_destroy=True)
    def perform_destroy(self, instance, **kwargs):
        super().perform_destroy(instance)


class RoomTypeViewSet(viewsets.ModelViewSet):
    queryset = RoomType.objects.all()
    serializer_class = RoomTypeSerializer
    permission_classes = (IsHotelier,)

    def get_queryset(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_hotelier:
                hotels = Hotel.objects.filter(hotelier=self.request.user.hoteliers.user_id)
                return RoomType.objects.filter(hotel__in=hotels)
        return super().get_queryset()

    @capture_validation_error
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @validate_hotelier()
    def perform_create(self, serializer, **kwargs):
        current_hotel = kwargs.get("hotel")
        serializer.save(hotel=current_hotel)

    @capture_validation_error
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @validate_hotelier()
    def perform_update(self, serializer, **kwargs):
        current_hotel = kwargs.get("hotel")
        serializer.save(hotel=current_hotel)

    @validate_hotelier(data={"model_name": RoomType, "id_name": "id", "id_value": "id"}, is_destroy=True)
    def perform_destroy(self, instance, **kwargs):
        super().perform_destroy(instance)
