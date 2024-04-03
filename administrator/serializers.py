from rest_framework import serializers
from .models import *


class ServicesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Services
        fields = "__all__"


class ImageCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = ImageCategory
        fields = "__all__"
