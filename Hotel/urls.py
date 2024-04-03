from django.urls import path
from .views import CoordinateViewSet

urlpatterns = [
    path("hotel_coordinates/", CoordinateViewSet.as_view({"get": "list"}), name="hotel_coordinates"),
]
