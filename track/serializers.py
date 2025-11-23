from rest_framework import serializers
from .models import Track


class TrackSerializer(serializers.ModelSerializer):
    artist = serializers.SerializerMethodField()
    album = serializers.SerializerMethodField()
    artist_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    album_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    duration_formatted = serializers.ReadOnlyField()

    class Meta:
        model = Track
        fields = [
            'track_id', 'artist', 'album', 'title', 'duration_sec', 'duration_formatted',
            'explicit', 'status', 'preview_url', 'audio_master_url', 'language',
            'genres', 'artist_id', 'album_id'
        ]
        read_only_fields = ['track_id']

    def get_artist(self, obj):
        """Importación diferida para evitar importaciones circulares"""
        from artist.serializers import ArtistSerializer
        if obj.artist_id:
            return ArtistSerializer(obj.artist_id).data
        return None

    def get_album(self, obj):
        """Importación diferida para evitar importaciones circulares"""
        from album.serializers import AlbumSerializer
        if obj.album_id:
            return AlbumSerializer(obj.album_id).data
        return None


class TrackCreateSerializer(serializers.ModelSerializer):
    artist_id = serializers.UUIDField(required=False, allow_null=True)
    album_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = Track
        fields = [
            'artist_id', 'album_id', 'title', 'duration_sec', 'explicit',
            'status', 'preview_url', 'audio_master_url', 'language', 'genres'
        ]

    def validate_duration_sec(self, value):
        if value <= 0:
            raise serializers.ValidationError("La duración debe ser mayor a 0 segundos")
        if value > 3600:  # 1 hora
            raise serializers.ValidationError("La duración no puede exceder 1 hora")
        return value

    def validate_audio_master_url(self, value):
        if not value:
            raise serializers.ValidationError("audio_master_url es obligatorio")
        return value

    def create(self, validated_data):
        # Extraer IDs de relaciones
        artist_id = validated_data.pop('artist_id', None)
        album_id = validated_data.pop('album_id', None)
        genres = validated_data.pop('genres', [])

        # Obtener instancias de artistas y álbumes
        if artist_id:
            try:
                from artist.models import Artist
                artist = Artist.objects.get(id=artist_id)
                validated_data['artist_id'] = artist
            except Artist.DoesNotExist:
                raise serializers.ValidationError({"artist_id": "Artista no encontrado"})
        else:
            validated_data['artist_id'] = None

        if album_id:
            try:
                from album.models import Album
                album = Album.objects.get(id=album_id)
                validated_data['album_id'] = album
            except Album.DoesNotExist:
                raise serializers.ValidationError({"album_id": "Álbum no encontrado"})
        else:
            validated_data['album_id'] = None

        # Crear el track
        track = Track.objects.create(**validated_data)

        # Agregar géneros si se proporcionaron
        if genres:
            track.genres.set(genres)

        return track


class TrackUpdateSerializer(serializers.ModelSerializer):
    artist_id = serializers.UUIDField(required=False, allow_null=True)
    album_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = Track
        fields = [
            'artist_id', 'album_id', 'title', 'duration_sec', 'explicit',
            'status', 'preview_url', 'audio_master_url', 'language', 'genres'
        ]

    def validate_duration_sec(self, value):
        if value and value <= 0:
            raise serializers.ValidationError("La duración debe ser mayor a 0 segundos")
        return value

    def update(self, instance, validated_data):
        # Manejar actualización de relaciones
        artist_id = validated_data.pop('artist_id', None)
        album_id = validated_data.pop('album_id', None)
        genres = validated_data.pop('genres', None)

        # Actualizar artista si se proporciona
        if artist_id is not None:
            if artist_id:
                try:
                    from artist.models import Artist
                    artist = Artist.objects.get(id=artist_id)
                    instance.artist_id = artist
                except Artist.DoesNotExist:
                    raise serializers.ValidationError({"artist_id": "Artista no encontrado"})
            else:
                instance.artist_id = None

        # Actualizar álbum si se proporciona
        if album_id is not None:
            if album_id:
                try:
                    from album.models import Album
                    album = Album.objects.get(id=album_id)
                    instance.album_id = album
                except Album.DoesNotExist:
                    raise serializers.ValidationError({"album_id": "Álbum no encontrado"})
            else:
                instance.album_id = None

        # Actualizar géneros si se proporcionan
        if genres is not None:
            instance.genres.set(genres)

        # Actualizar los demás campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance