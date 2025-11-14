from django.contrib import admin
from .models import Artist


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'country', 'get_label', 'albums_count',
        'tracks_count', 'is_signed'
    ]
    list_filter = ['country', 'label_id']
    search_fields = ['name', 'bio']
    readonly_fields = ['artist_id', 'albums_count', 'tracks_count', 'is_signed', 'public_social_media']

    fieldsets = (
        ('Información Básica', {
            'fields': ('artist_id', 'name', 'bio', 'image_url')
        }),
        ('Ubicación y Sello', {
            'fields': ('country', 'label_id')
        }),
        ('Redes Sociales', {
            'fields': ('socials', 'public_social_media')
        }),
        ('Estadísticas', {
            'fields': ('albums_count', 'tracks_count', 'is_signed'),
            'classes': ('collapse',)
        }),
    )

    def get_label(self, obj):
        return obj.label_id.name if obj.label_id else "Independiente"

    get_label.short_description = 'Sello'
    get_label.admin_order_field = 'label_id__name'