from django.contrib import admin
from .models import RecordLabel


@admin.register(RecordLabel)
class RecordLabelAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'country', 'contact', 'web',
        'artists_count', 'albums_count', 'is_active'
    ]
    list_filter = ['country', 'created_at']
    search_fields = ['name', 'contact', 'web']
    readonly_fields = ['id', 'artists_count', 'albums_count', 'is_active']

    fieldsets = (
        ('Información Básica', {
            'fields': ('id', 'name', 'country')
        }),
        ('Contacto', {
            'fields': ('contact', 'web')
        }),
        ('Estadísticas', {
            'fields': ('artists_count', 'albums_count', 'is_active'),
            'classes': ('collapse',)
        }),
    )