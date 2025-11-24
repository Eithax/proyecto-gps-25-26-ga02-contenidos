from rest_framework import serializers
from .models import Album


class AlbumSerializer(serializers.ModelSerializer):
    # Campos de solo lectura para representación
    artist = serializers.SerializerMethodField()

    # Campos calculados
    total_tracks = serializers.ReadOnlyField()
    total_duration = serializers.ReadOnlyField()
    duration_formatted = serializers.ReadOnlyField()
    is_released = serializers.ReadOnlyField()

    # Campos para escritura
    # artist_id = serializers.UUIDField(write_only=True, required=True)
    artist_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Album
        fields = [
            'id', 'artist', 'title', 'cover_url', 'release_date',
            'status', 'genres', 'price', 'total_tracks', 'total_duration',
            'duration_formatted', 'is_released', 'created_at', 'updated_at',
            'artist_id'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_artist(self, obj):
        """Importación diferida para evitar importaciones circulares"""
        from artist.serializers import ArtistSerializer
        return ArtistSerializer(obj.artist).data


class AlbumCreateSerializer(serializers.ModelSerializer):
    # artist_id = serializers.UUIDField(required=True)
    artist_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Album
        fields = [
            'id', 'artist_id', 'title', 'cover_url', 'release_date',
            'status', 'genres', 'price'
        ]

    def validate_price(self, value):
        """Validar que el precio no sea negativo"""
        if value < 0:
            raise serializers.ValidationError("El precio no puede ser negativo")
        return value

    def create(self, validated_data):
        # Extraer artist_id
        artist_id = validated_data.pop('artist_id')
        genres = validated_data.pop('genres', [])

        # Obtener instancia del artista
        try:
            from artist.models import Artist
            artist = Artist.objects.get(id=artist_id)
            validated_data['artist'] = artist
        except Artist.DoesNotExist:
            raise serializers.ValidationError({"artist_id": "Artista no encontrado"})

        # Crear el álbum
        album = Album.objects.create(**validated_data)

        # Agregar géneros si se proporcionaron
        if genres:
            album.genres.set(genres)

        return album


class AlbumUpdateSerializer(serializers.ModelSerializer):
    # artist_id = serializers.UUIDField(required=False)
    artist_id = serializers.ReadOnlyField()

    class Meta:
        model = Album
        fields = [
            'artist_id', 'title', 'cover_url', 'release_date',
            'status', 'genres', 'price'
        ]

    def validate_release_date(self, value):
        from django.utils import timezone
        if value and value < timezone.now().date():
            raise serializers.ValidationError(
                "La fecha de lanzamiento no puede ser en el pasado"
            )
        return value

    def validate_price(self, value):
        if value and value < 0:
            raise serializers.ValidationError("El precio no puede ser negativo")
        return value

    def update(self, instance, validated_data):
        # Manejar actualización del artista si se proporciona
        artist_id = validated_data.pop('artist_id', None)
        genres = validated_data.pop('genres', None)

        if artist_id is not None:
            try:
                from artist.models import Artist
                artist = Artist.objects.get(id=artist_id)
                instance.artist = artist
            except Artist.DoesNotExist:
                raise serializers.ValidationError({"artist_id": "Artista no encontrado"})

        # Actualizar géneros si se proporcionan
        if genres is not None:
            instance.genres.set(genres)

        # Actualizar los demás campos
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class AlbumSongsSerializer(serializers.ModelSerializer):
    """Serializer para el endpoint que incluye álbum + canciones"""
    artist = serializers.SerializerMethodField()
    songs = serializers.SerializerMethodField()

    class Meta:
        model = Album
        fields = [
            'id', 'artist', 'title', 'cover_url', 'release_date',
            'status', 'genres', 'price', 'songs', 'created_at', 'updated_at'
        ]

    def get_artist(self, obj):
        """Importación diferida para artista"""
        from artist.serializers import ArtistSerializer
        return ArtistSerializer(obj.artist).data

    def get_songs(self, obj):
        """Importación diferida para tracks"""
        from track.serializers import TrackSerializer
        tracks = obj.tracks.all()
        return TrackSerializer(tracks, many=True).data