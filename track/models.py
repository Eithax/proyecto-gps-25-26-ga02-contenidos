from django.db import models
from core.choices import ReleaseStatus, Language

class Track(models.Model):
    track_id = models.AutoField(primary_key=True)
    artist_id = models.ForeignKey('artist.Artist', on_delete=models.SET_NULL, null=True, blank=True, related_name='tracks')
    album_id = models.ForeignKey('album.Album', on_delete=models.SET_NULL, null=True, blank=True, related_name='tracks')
    title = models.CharField(max_length=200, blank=False, null=False)
    duration_sec = models.PositiveIntegerField(default=0)
    explicit = models.BooleanField(default=False)
    status = models.CharField(
        max_length=10,
        choices=ReleaseStatus.choices,
        default=ReleaseStatus.PUBLISHED
    )
    preview_url = models.URLField(max_length=1000, null=True, blank=True)
    audio_master_url = models.URLField(max_length=1000, null=False, blank=False)
    language = models.CharField(
        max_length=2,
        choices=Language.choices,
        default=Language.ENGLISH
    )
    genres = models.ManyToManyField(
        'genre.Genre',
        related_name='tracks',
        blank=True
    )

    class Meta:
        db_table = 'tracks'
        ordering = ['title']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['status']),
            models.Index(fields=['artist_id', 'album_id']),
        ]

    def __str__(self):
        return f"{self.title} - {self.artist_id.name}"

    @property
    def duration_formatted(self):
        """Devuelve la duración en formato MM:SS"""
        minutes = self.duration_sec // 60
        seconds = self.duration_sec % 60
        return f"{minutes:02d}:{seconds:02d}"