from django.utils import timezone
from django.db import models
import uuid


class Genre(models.Model):
    # ID único
    #genre_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    genre_id = models.AutoField(primary_key=True)

    # Campos básicos
    name = models.CharField(
        max_length=100,
        blank=False,
        null=False,
        unique=True,
        help_text="Nombre del género musical"
    )
    description = models.TextField(
        max_length=550,
        blank=True,
        null=False,
        help_text="Descripción del género musical"
    )

    # Relación padre-hijo para subgéneros
    parent_genre = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subgenres',
        verbose_name='Género padre'
    )

    # Campos de auditoría
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'genres'
        ordering = ['name']
        verbose_name = 'Género Musical'
        verbose_name_plural = 'Géneros Musicales'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['parent_genre']),
        ]

    def __str__(self):
        return self.name

    @property
    def is_subgenre(self):
        """Verifica si es un subgénero"""
        return self.parent_genre is not None

    @property
    def full_hierarchy(self):
        """Devuelve la jerarquía completa del género"""
        hierarchy = []
        current = self
        while current:
            hierarchy.insert(0, current.name)
            current = current.parent_genre
        return ' → '.join(hierarchy)

    @property
    def tracks_count(self):
        """Número total de pistas con este género"""
        return self.tracks.count()

    @property
    def albums_count(self):
        """Número total de álbumes con este género"""
        return self.albums.count()

    def get_all_subgenres(self):
        """Obtiene todos los subgéneros recursivamente"""
        subgenres = list(self.subgenres.all())
        for subgenre in self.subgenres.all():
            subgenres.extend(subgenre.get_all_subgenres())
        return subgenres

    def get_all_tracks(self):
        """Obtiene todas las pistas de este género y sus subgéneros"""
        from track.models import Track
        genre_ids = [self.genre_id] + [sg.genre_id for sg in self.get_all_subgenres()]
        return Track.objects.filter(genres__genre_id__in=genre_ids).distinct()