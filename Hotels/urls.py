"""
URL configuration for Hotels project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from django.conf import settings
from django.conf.urls.static import static
from Hotel.views import HotelViewSet, ServicesHotelViewSet, ImageViewSet, RoomTypeViewSet


# Api router
router = routers.DefaultRouter()
router.register(r"hotels", HotelViewSet)
router.register(r"hotel_services", ServicesHotelViewSet)
router.register(r"hotel_images", ImageViewSet)
router.register(r"hotel_room-type", RoomTypeViewSet)

urlpatterns = [
    # Admin routes
    path('admin/', admin.site.urls),
    # Api routes
    path("api/v1/", include("authentication.urls")),
    path("api/v1/", include("administrator.urls")),
    path("api/v1/", include(router.urls)),
    path("api/v1/", include("Hotel.urls")),
    path("api/v1/", include("payments.urls")),
]

# Server static files in development server
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
