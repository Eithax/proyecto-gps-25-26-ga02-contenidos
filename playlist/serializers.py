from rest_framework import serializers
from .models import Playlist, PlaylistTrack
from .services.user_service import UserService


class PlaylistCreateSerializer(serializers.ModelSerializer):
    owner_id = serializers.CharField(required=True, max_length=100)

    class Meta:
        model = Playlist
        fields = ['id', 'owner_id', 'title', 'description', 'is_public']

    def validate_owner_id(self, value):
        """Valida que el user_id exista y tenga formato adecuado"""
        if not value or not value.strip():
            raise serializers.ValidationError("El ID de usuario es requerido")

        # Validación de formato básica
        # TODO: Revisar reglas
        if len(value) > 100:
            raise serializers.ValidationError("El ID de usuario es demasiado largo")

        return value.strip()

    def validate_title(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("El título es requerido")
        return value.strip()


class PlaylistSerializer(serializers.ModelSerializer):
    tracks_count = serializers.SerializerMethodField()
    total_duration = serializers.SerializerMethodField()

    class Meta:
        model = Playlist
        fields = [
            'id', 'owner_id', 'title', 'description',
            'is_public', 'tracks_count', 'total_duration', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_tracks_count(self, obj):
        return obj.tracks.count()

    def get_total_duration(self, obj):
        from django.db.models import Sum
        total = obj.tracks.aggregate(total=Sum('duration_sec'))['total']
        return total or 0


class PlaylistTrackSerializer(serializers.ModelSerializer):
    track_info = serializers.SerializerMethodField()

    class Meta:
        model = PlaylistTrack
        fields = ['id', 'position', 'added_at', 'track_info']

    def get_track_info(self, obj):
        from track.serializers import TrackSerializer
        return TrackSerializer(obj.track).data


class PlaylistDetailSerializer(PlaylistSerializer):
    tracks = serializers.SerializerMethodField()

    class Meta(PlaylistSerializer.Meta):
        fields = PlaylistSerializer.Meta.fields + ['tracks']

    def get_tracks(self, obj):
        playlist_tracks = obj.playlist_tracks.select_related('track').order_by('position')
        return PlaylistTrackSerializer(playlist_tracks, many=True).data


class PlaylistPublicSerializer(serializers.ModelSerializer):
    """Serializer para playlists públicas (sin owner_id)"""
    tracks_count = serializers.ReadOnlyField()
    total_duration_formatted = serializers.ReadOnlyField()

    class Meta:
        model = Playlist
        fields = [
            'id', 'title', 'description', 'tracks_count',
            'total_duration_formatted', 'created_at'
        ]
        read_only_fields = fields