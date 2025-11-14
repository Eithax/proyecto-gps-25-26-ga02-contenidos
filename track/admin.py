from django.contrib import admin
from .models import Track


@admin.register(Track)
class TrackAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'get_artist', 'get_album', 'duration_formatted',
        'language', 'explicit', 'status'
    ]
    list_filter = ['status', 'language', 'explicit']
    search_fields = ['title', 'artist_id__name', 'album_id__title']
    filter_horizontal = ['genres']
    readonly_fields = ['duration_formatted']

    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'artist_id', 'album_id', 'duration_sec')
        }),
        ('Contenido', {
            'fields': ('preview_url', 'audio_master_url', 'genres')
        }),
        ('Metadatos', {
            'fields': ('language', 'explicit', 'status')
        }),
    )

    def get_artist(self, obj):
        return obj.artist_id.name if obj.artist_id else "Sin artista"

    get_artist.short_description = 'Artista'
    get_artist.admin_order_field = 'artist_id__name'

    def get_album(self, obj):
        return obj.album_id.title if obj.album_id else "Sin álbum"

    get_album.short_description = 'Álbum'
    get_album.admin_order_field = 'album_id__title'