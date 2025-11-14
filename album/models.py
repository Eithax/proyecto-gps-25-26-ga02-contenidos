from django.db import models
from django.conf import settings
from core.choices import ReleaseStatus
import uuid


class Album(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    artist_id = models.ForeignKey(
        'artist.Artist',
        on_delete=models.CASCADE,
        related_name='albums'
    )
    title = models.CharField(max_length=255)
    cover_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="URL de la portada del álbum"
    )
    release_date = models.DateField()
    status = models.CharField(
        max_length=10,
        choices=ReleaseStatus.choices,
        default=ReleaseStatus.DRAFT
    )
    price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00,
        help_text="Precio del álbum en la moneda base"
    )
    genres = models.ManyToManyField(
        'genre.Genre',
        related_name='albums',
        blank=True
    )
    track_list = models.ManyToManyField(
        'track.Track',
        related_name='tracks',
        blank=True
    )

    # Campos de auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'albums'
        ordering = ['-release_date', 'title']
        verbose_name = 'Álbum'
        verbose_name_plural = 'Álbumes'
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['release_date']),
            models.Index(fields=['status']),
            models.Index(fields=['artist_id', 'release_date']),
        ]

    def __str__(self):
        return f"{self.title} - {self.artist_id.name}"

    @property
    def is_released(self):
        """Verifica si el álbum ya fue lanzado"""
        from django.utils import timezone
        if self.release_date is None:
            return False
        return self.release_date <= timezone.now().date()

    @property
    def total_duration(self):
        """Calcula la duración total del álbum sumando las pistas"""
        from django.db.models import Sum
        total_seconds = self.tracks.aggregate(
            total=Sum('duration_sec')
        )['total'] or 0
        return total_seconds

    @property
    def total_tracks(self):
        """Número total de pistas en el álbum"""
        return self.tracks.count()

    @property
    def duration_formatted(self):
        """Duración total formateada en HH:MM:SS"""
        total_seconds = self.total_duration
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    def get_tracks_ordered(self):
        """Obtiene las pistas ordenadas (podrías agregar un campo 'track_number' después)"""
        return self.tracks.all().order_by('title')