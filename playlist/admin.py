# playlist/admin.py
from django.contrib import admin
from .models import Playlist, PlaylistTrack


@admin.register(PlaylistTrack)
class PlaylistTrackAdmin(admin.ModelAdmin):
    list_display = ['playlist', 'track', 'position', 'added_at']
    list_filter = ['playlist', 'added_at']
    search_fields = ['playlist__title', 'track__title']
    ordering = ['playlist', 'position']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('playlist', 'track')


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'owner_id', 'is_public', 'tracks_count',
        'total_duration_formatted', 'created_at'
    ]
    list_filter = ['is_public', 'created_at']
    search_fields = ['title', 'description', 'owner_id']
    readonly_fields = ['tracks_count', 'total_duration_formatted']

    fieldsets = (
        ('Información Básica', {
            'fields': ('title', 'owner_id', 'description', 'is_public')
        }),
        ('Estadísticas', {
            'fields': ('tracks_count', 'total_duration_formatted'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            tracks_count=Count('playlist_tracks'),
            total_duration=Sum('playlist_tracks__track__duration_sec')
        )