from django.db import models

# Create your models here.
class Services(models.Model):
    name = models.CharField(max_length=30, unique=True, verbose_name="Nombre")

    class Meta:
        verbose_name = "Servicio"

    def __str__(self):
        return str(self.name)


class ImageCategory(models.Model):
    name = models.CharField(max_length=30, unique=True, verbose_name="Categoría")

    class Meta:
        verbose_name = "Categoría de imagen"
        verbose_name_plural = "Categorías de imágenes"
        ordering = ["name"]

    def __str__(self):
        return str(self.name)
