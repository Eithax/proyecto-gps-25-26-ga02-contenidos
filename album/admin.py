from django.contrib import admin
from .models import Album


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'artist_id', 'release_date', 'status',
        'total_tracks', 'duration_formatted', 'price'
    ]
    list_filter = ['status', 'release_date', 'artist_id']
    search_fields = ['title', 'artist_id__name']
    filter_horizontal = ['genres']
    readonly_fields = ['total_tracks', 'total_duration', 'duration_formatted', 'is_released']
    date_hierarchy = 'release_date'

    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'artist_id', 'release_date', 'cover_url')
        }),
        ('Detalles', {
            'fields': ('status', 'price', 'genres')
        }),
        ('Estadísticas', {
            'fields': ('total_tracks', 'total_duration', 'duration_formatted', 'is_released'),
            'classes': ('collapse',)
        }),
    )