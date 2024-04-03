from django.contrib import admin
from .models import Services, ImageCategory

# Register your models here.
class ServicesAdmin(admin.ModelAdmin):
    pass


class ImageCategoryAdmin(admin.ModelAdmin):
    pass

admin.site.register(Services, ServicesAdmin)
admin.site.register(ImageCategory, ImageCategoryAdmin)
