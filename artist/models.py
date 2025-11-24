from django.db import models
import uuid


class Artist(models.Model):
    # ID único
    #artist_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id = models.AutoField(primary_key=True, db_column='artist_id')

    # Campos básicos
    name = models.CharField(max_length=200, blank=False, null=False)
    bio = models.TextField(max_length=1000, blank=True, null=False)
    image_url = models.URLField(
        null=False,
        blank=False,
        default='https://static.vecteezy.com/system/resources/previews/036/280/651/original/default-avatar-profile-icon-social-media-user-image-gray-avatar-icon-blank-profile-silhouette-illustration-vector.jpg'
    )

    # Relaciones
    label = models.ForeignKey(
        "record_label.RecordLabel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='artists',
        db_column='label_id'
    )
    country = models.ForeignKey(
        "country.Country",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='artists'
    )

    # Redes sociales
    socials = models.JSONField(
        default=dict,
        blank=True,
        null=False,
        help_text='Diccionario con las redes sociales: {\'twitter\': \'url\', ...}'
    )

    # Campos de auditoría
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'artists'
        ordering = ['name']
        verbose_name = 'Artista'
        verbose_name_plural = 'Artistas'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['country']),
            models.Index(fields=['label_id']),
        ]

    def __str__(self):
        return self.name

    def add_social_media(self, social_media, url):
        """Añadir una red social"""
        self.socials[social_media] = url
        self.save()

    def get_social_media(self, social_media):
        """Obtener URL de una red social específica"""
        return self.socials.get(social_media)

    def remove_social_media(self, social_media):
        """Eliminar una red social"""
        if social_media in self.socials:
            del self.socials[social_media]
            self.save()

    @property
    def public_social_media(self):
        """Redes sociales con URL (no vacías)"""
        return {k: v for k, v in self.socials.items() if v}

    @property
    def is_signed(self):
        """Verifica si el artista está firmado con un sello"""
        return self.label_id is not None