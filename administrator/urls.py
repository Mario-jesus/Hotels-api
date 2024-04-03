from django.urls import path
from .views import ServicesViewSet, ImageCategoryViewSet

urlpatterns = [
    path("services/", ServicesViewSet.as_view({"get": "list"}), name="services"),
    path("image-categories/", ImageCategoryViewSet.as_view({"get": "list"}), name="image_categories"),
]
