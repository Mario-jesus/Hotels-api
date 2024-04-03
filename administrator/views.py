from rest_framework import viewsets
from .models import Services, ImageCategory
from .serializers import ServicesSerializer, ImageCategorySerializer

# Create your views here.
class ServicesViewSet(viewsets.ModelViewSet):
    queryset = Services.objects.all().order_by('name')
    serializer_class = ServicesSerializer


class ImageCategoryViewSet(viewsets.ModelViewSet):
    queryset = ImageCategory.objects.all()
    serializer_class = ImageCategorySerializer
