from django.db import models

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