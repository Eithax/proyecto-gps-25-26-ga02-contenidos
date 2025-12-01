from django.db import models
from django.db.models import Sum, Count

# Create your models here.
class Playlist(models.Model):
    id = models.AutoField(primary_key=True)
    owner_id = models.CharField(
        max_length=100,
        db_index=True,
        help_text="ID del usuario en el microservicio de autenticación (formato string)"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, max_length=500)
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'playlists'
        indexes = [
            models.Index(fields=['owner_id', 'created_at']),
            models.Index(fields=['owner_id', 'is_public']),
        ]

    def __str__(self):
        return f"{self.title} (Owner: {self.owner_id})"

    # === PROPIEDADES CALCULADAS ===

    @property
    def tracks_count(self):
        """Número total de tracks en la playlist"""
        return self.playlist_tracks.count()

    @property
    def total_duration(self):
        """Duración total de la playlist en segundos"""
        result = self.playlist_tracks.aggregate(
            total_duration=Sum('track__duration_sec')
        )
        return result['total_duration'] or 0

    @property
    def total_duration_formatted(self):
        """Duración total formateada (HH:MM:SS)"""
        total_seconds = self.total_duration
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"

    # === MÉTODOS DE GESTIÓN DE TRACKS ===

    def get_tracks_ordered(self):
        """Obtener todos los tracks ordenados por posición"""
        return [pt.track for pt in self.playlist_tracks.select_related(
            'track', 'track__artist', 'track__album'
        ).order_by('position')]

    def get_tracks_with_positions(self):
        """Obtener tracks con información de posición"""
        return self.playlist_tracks.select_related(
            'track', 'track__artist', 'track__album'
        ).order_by('position')

    def add_track(self, track, position=0):
        """Añadir un track a la playlist"""
        playlist_track, created = PlaylistTrack.objects.get_or_create(
            playlist=self,
            track=track,
            defaults={'position': position}
        )
        return playlist_track, created

    def remove_track(self, track):
        """Eliminar un track de la playlist"""
        deleted_count, _ = PlaylistTrack.objects.filter(
            playlist=self,
            track=track
        ).delete()
        return deleted_count > 0

    def move_track(self, track, new_position):
        """Mover un track a una nueva posición"""
        try:
            playlist_track = PlaylistTrack.objects.get(
                playlist=self,
                track=track
            )

            # Reordenar las demás posiciones si es necesario
            if new_position < playlist_track.position:
                # Mover hacia arriba
                PlaylistTrack.objects.filter(
                    playlist=self,
                    position__gte=new_position,
                    position__lt=playlist_track.position
                ).update(position=models.F('position') + 1)
            elif new_position > playlist_track.position:
                # Mover hacia abajo
                PlaylistTrack.objects.filter(
                    playlist=self,
                    position__gt=playlist_track.position,
                    position__lte=new_position
                ).update(position=models.F('position') - 1)

            playlist_track.position = new_position
            playlist_track.save()
            return True

        except PlaylistTrack.DoesNotExist:
            return False

    def clear_tracks(self):
        """Eliminar todos los tracks de la playlist"""
        return self.playlist_tracks.all().delete()

    def contains_track(self, track):
        """Verificar si la playlist contiene un track específico"""
        return self.playlist_tracks.filter(track=track).exists()

    def get_track_position(self, track):
        """Obtener la posición de un track en la playlist"""
        try:
            playlist_track = self.playlist_tracks.get(track=track)
            return playlist_track.position
        except PlaylistTrack.DoesNotExist:
            return None

    # === MÉTODOS DE BÚSQUEDA ===

    @classmethod
    def get_user_playlists(cls, owner_id):
        """Obtener todas las playlists de un usuario"""
        return cls.objects.filter(owner_id=owner_id).prefetch_related(
            'playlist_tracks__track'
        )

    @classmethod
    def get_public_playlists(cls):
        """Obtener todas las playlists públicas"""
        return cls.objects.filter(is_public=True).annotate(
            tracks_count=Count('playlist_tracks')
        ).prefetch_related('playlist_tracks__track')

    @classmethod
    def search_public_playlists(cls, query):
        """Buscar playlists públicas por título o descripción"""
        return cls.objects.filter(
            is_public=True
        ).filter(
            models.Q(title__icontains=query) |
            models.Q(description__icontains=query)
        ).annotate(
            tracks_count=Count('playlist_tracks')
        ).prefetch_related('playlist_tracks__track')


class PlaylistTrack(models.Model):
    playlist = models.ForeignKey(
        'Playlist',
        on_delete=models.CASCADE,
        related_name='playlist_tracks'
    )
    track = models.ForeignKey(
        'track.Track',  # Asumiendo que tu app de tracks se llama 'tracks'
        on_delete=models.CASCADE,
        related_name='playlist_entries'
    )
    position = models.PositiveIntegerField(
        default=0,
        help_text="Posición del track en la playlist (0 = auto)"
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'playlist_tracks'
        ordering = ['playlist', 'position']
        unique_together = ['playlist', 'track']  # Evita duplicados
        indexes = [
            models.Index(fields=['playlist', 'position']),
            models.Index(fields=['added_at']),
        ]
        verbose_name = 'Track en Playlist'
        verbose_name_plural = 'Tracks en Playlists'

    def __str__(self):
        return f"'{self.track.title}' en '{self.playlist.title}' (Pos: {self.position})"

    def save(self, *args, **kwargs):
        """Auto-generar posición si no se especifica"""
        if self.position == 0:
            # Encontrar la última posición en esta playlist
            last_position = PlaylistTrack.objects.filter(
                playlist=self.playlist
            ).aggregate(models.Max('position'))['position__max'] or 0
            self.position = last_position + 1
        super().save(*args, **kwargs)