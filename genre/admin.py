from django.contrib import admin
from .models import Genre


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'parent_genre', 'is_subgenre',
        'tracks_count', 'albums_count', 'created_at'
    ]
    list_filter = ['parent_genre', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = [
        'genre_id', 'is_subgenre', 'full_hierarchy',
        'tracks_count', 'albums_count'
    ]

    fieldsets = (
        ('Información Básica', {
            'fields': ('genre_id', 'name', 'description')
        }),
        ('Jerarquía', {
            'fields': ('parent_genre', 'is_subgenre', 'full_hierarchy')
        }),
        ('Estadísticas', {
            'fields': ('tracks_count', 'albums_count'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent_genre')