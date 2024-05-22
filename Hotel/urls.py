from django.urls import path
from .views import CoordinateViewSet, AllHotelsViewSet

urlpatterns = [
    path("hotel_coordinates/", CoordinateViewSet.as_view({"get": "list"}), name="hotel_coordinates"),
    path("all_hotels/", AllHotelsViewSet.as_view({"get": "list"}), name="all_hotels"),
    path("all_hotels/<slug:pk>/", AllHotelsViewSet.as_view({"get": "retrieve"}), name="all_hotels"),
]
