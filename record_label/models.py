from django.db import models
import uuid


class RecordLabel(models.Model):
    # ID único
    label_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Campos básicos
    name = models.CharField(max_length=200, blank=False, null=False)
    contact = models.EmailField(max_length=200, blank=True, null=False)
    web = models.URLField(max_length=200, blank=True, null=False)

    # Relación con país
    country = models.ForeignKey(
        'country.Country',
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        related_name='record_labels'
    )

    # Campos de auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'record_labels'
        ordering = ['name']
        verbose_name = 'Sello Discográfico'
        verbose_name_plural = 'Sellos Discográficos'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['country']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.name

    @property
    def artists_count(self):
        """Número total de artistas firmados con el sello"""
        return self.artists.count()

    @property
    def albums_count(self):
        """Número total de álbumes publicados por el sello"""
        from album.models import Album
        return Album.objects.filter(artist__label_id=self).count()

    @property
    def is_active(self):
        """Verifica si el sello tiene artistas activos"""
        return self.artists_count > 0