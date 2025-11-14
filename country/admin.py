from django.contrib import admin
from .models import Country


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'iso_code', 'continent', 'currency_code',
        'artists_count', 'record_labels_count', 'is_active'
    ]
    list_filter = ['continent', 'is_active', 'created_at']
    search_fields = ['name', 'iso_code', 'iso_code_3']
    readonly_fields = [
        'id', 'artists_count', 'record_labels_count', 'full_info'
    ]
    list_editable = ['is_active']

    fieldsets = (
        ('Información Básica', {
            'fields': ('id', 'name', 'iso_code', 'iso_code_3', 'continent')
        }),
        ('Información Adicional', {
            'fields': ('phone_code', 'currency_code', 'currency_name', 'flag_url')
        }),
        ('Estado', {
            'fields': ('is_active',)
        }),
        ('Estadísticas', {
            'fields': ('artists_count', 'record_labels_count', 'full_info'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('artists', 'record_labels')