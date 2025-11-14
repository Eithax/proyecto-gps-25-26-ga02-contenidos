import django_filters
from .models import Track


class TrackFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    artist_name = django_filters.CharFilter(field_name='artist__name', lookup_expr='icontains')
    album_title = django_filters.CharFilter(field_name='album__title', lookup_expr='icontains')
    genre = django_filters.CharFilter(field_name='genres__name', lookup_expr='icontains')
    min_duration = django_filters.NumberFilter(field_name='duration_sec', lookup_expr='gte')
    max_duration = django_filters.NumberFilter(field_name='duration_sec', lookup_expr='lte')

    class Meta:
        model = Track
        fields = ['title', 'artist_id', 'album_id', 'language', 'explicit', 'status']