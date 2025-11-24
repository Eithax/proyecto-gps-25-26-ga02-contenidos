from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Artist
from .serializers import (
    ArtistSerializer,
    ArtistCreateSerializer,
    ArtistUpdateSerializer
)


class ArtistViewSet(viewsets.ModelViewSet):
    queryset = Artist.objects.select_related('label', 'country')
    serializer_class = ArtistSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return ArtistCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ArtistUpdateSerializer
        return ArtistSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtros según query parameters
        genre = self.request.query_params.get('genre')
        query = self.request.query_params.get('query')

        if genre:
            # Filtrar artistas por género de sus pistas
            queryset = queryset.filter(
                Q(tracks__genres__name__icontains=genre) |
                Q(albums__genres__name__icontains=genre)
            ).distinct()

        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(bio__icontains=query)
            )

        return queryset

    def list(self, request, *args, **kwargs):
        """
        GET /artists - Buscar artistas
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Paginación
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        POST /artists - Crear artista
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            artist = serializer.save()
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar duplicados (puedes personalizar esta lógica)
        if Artist.objects.filter(name=artist.name).count() > 1:
            return Response(
                {'error': 'Ya existe un artista con este nombre'},
                status=status.HTTP_409_CONFLICT
            )

        read_serializer = ArtistSerializer(artist)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        """
        GET /artists/{artist_id} - Obtener detalles de un artista
        """
        artist = self.get_object()
        serializer = self.get_serializer(artist)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """
        PATCH /artists/{artist_id} - Actualizar artista
        """
        artist = self.get_object()
        serializer = self.get_serializer(artist, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            artist = serializer.save()
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        read_serializer = ArtistSerializer(artist)
        return Response(read_serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        DELETE /artists/{artist_id} - Eliminar artista
        """
        artist = self.get_object()
        artist.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def add_social(self, request, pk=None):
        """
        POST /artists/{artist_id}/socials - Añadir red social
        """
        artist = self.get_object()
        social_media = request.data.get('platform')
        url = request.data.get('url')

        if not social_media or not url:
            return Response(
                {'error': 'Se requieren platform y url'},
                status=status.HTTP_400_BAD_REQUEST
            )

        artist.add_social_media(social_media, url)
        serializer = self.get_serializer(artist)
        return Response(serializer.data)

    @action(detail=True, methods=['delete'])
    def remove_social(self, request, pk=None):
        """
        DELETE /artists/{artist_id}/socials/{platform} - Eliminar red social
        """
        artist = self.get_object()
        platform = request.data.get('platform') or request.query_params.get('platform')

        if not platform:
            return Response(
                {'error': 'Se requiere el parámetro platform'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if platform not in artist.socials:
            return Response(
                {'error': 'Red social no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )

        artist.remove_social_media(platform)
        serializer = self.get_serializer(artist)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def albums(self, request, pk=None):
        """
        GET /artists/{artist_id}/albums - Obtener álbumes del artista
        """
        artist = self.get_object()
        from album.serializers import AlbumSerializer
        albums = artist.albums.all()

        page = self.paginate_queryset(albums)
        if page is not None:
            serializer = AlbumSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AlbumSerializer(albums, many=True)
        return Response({
            'items': serializer.data,
            'total': albums.count()
        })

    @action(detail=True, methods=['get'])
    def tracks(self, request, pk=None):
        """
        GET /artists/{artist_id}/tracks - Obtener pistas del artista
        """
        artist = self.get_object()
        from track.serializers import TrackSerializer
        tracks = artist.tracks.all()

        page = self.paginate_queryset(tracks)
        if page is not None:
            serializer = TrackSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = TrackSerializer(tracks, many=True)
        return Response({
            'items': serializer.data,
            'total': tracks.count()
        })