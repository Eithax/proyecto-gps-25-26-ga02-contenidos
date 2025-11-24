from django.contrib import admin
from .models import Artist


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'country', 'get_label', 'is_signed'
    ]
    list_filter = ['country', 'label_id']
    search_fields = ['name', 'bio']
    readonly_fields = ['id', 'is_signed', 'public_social_media']

    fieldsets = (
        ('Información Básica', {
            'fields': ('id', 'name', 'bio', 'image_url')
        }),
        ('Ubicación y Sello', {
            'fields': ('country', 'label')
        }),
        ('Redes Sociales', {
            'fields': ('socials', 'public_social_media')
        }),
        ('Estadísticas', {
            'fields': ('is_signed',),
            'classes': ('collapse',)
        }),
    )

    def get_label(self, obj):
        return obj.label.name if obj.label_id else "Independiente"

    get_label.short_description = 'Sello'
    get_label.admin_order_field = 'label_id__name'