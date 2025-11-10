from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Track
from .serializers import (
    TrackSerializer,
    TrackCreateSerializer,
    TrackUpdateSerializer
)


class TrackViewSet(viewsets.ModelViewSet):
    queryset = Track.objects.select_related('artist_id', 'album_id').prefetch_related('genres')
    serializer_class = TrackSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return TrackCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return TrackUpdateSerializer
        return TrackSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtros según query parameters
        album_id = self.request.query_params.get('album_id')
        artist_id = self.request.query_params.get('artist_id')
        genre = self.request.query_params.get('genre')
        status = self.request.query_params.get('status')

        if album_id:
            queryset = queryset.filter(album_id=album_id)
        if artist_id:
            queryset = queryset.filter(artist_id=artist_id)
        if genre:
            queryset = queryset.filter(genres__name__icontains=genre)
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def list(self, request, *args, **kwargs):
        """
        GET /tracks - Listar todas las canciones
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Paginación
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'items': serializer.data,
            'total': queryset.count()
        })

    def create(self, request, *args, **kwargs):
        """
        POST /tracks - Subir metadatos de una canción
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            track = serializer.save()
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Devolver el track creado con el serializer de lectura
        read_serializer = TrackSerializer(track)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        """
        GET /tracks/{track_id} - Obtener detalles de una canción
        """
        track = self.get_object()
        serializer = self.get_serializer(track)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """
        PATCH /tracks/{track_id} - Actualizar canción
        """
        track = self.get_object()
        serializer = self.get_serializer(track, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            track = serializer.save()
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        read_serializer = TrackSerializer(track)
        return Response(read_serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        DELETE /tracks/{track_id} - Eliminar canción
        """
        track = self.get_object()
        track.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Búsqueda avanzada de tracks por título, artista o álbum
        """
        query = request.query_params.get('q', '')
        queryset = self.get_queryset()

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(artist_id__name__icontains=query) |
                Q(album_id__title__icontains=query)
            )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'items': serializer.data,
            'total': queryset.count()
        })