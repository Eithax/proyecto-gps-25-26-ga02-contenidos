from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Album
from .serializers import (
    AlbumSerializer,
    AlbumCreateSerializer,
    AlbumUpdateSerializer,
    AlbumSongsSerializer
)


class AlbumViewSet(viewsets.ModelViewSet):
    queryset = Album.objects.select_related('artist').prefetch_related('genres', 'tracks')
    serializer_class = AlbumSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return AlbumCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AlbumUpdateSerializer
        elif self.action == 'album_songs':
            return AlbumSongsSerializer
        return AlbumSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtros según query parameters
        artist_id = self.request.query_params.get('artist_id')
        status = self.request.query_params.get('status')

        if artist_id:
            queryset = queryset.filter(artist_id=artist_id)
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def list(self, request, *args, **kwargs):
        """
        GET /albums - Listar álbumes
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

    def retrieve(self, request, *args, **kwargs):
        """
        GET /albums/{album_id} - Obtener detalles de un álbum
        """
        album = self.get_object()
        serializer = self.get_serializer(album)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        POST /albums - Crear un álbum
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            album = serializer.save()
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        read_serializer = AlbumSerializer(album)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        """
        PATCH /albums/{id} - Actualizar álbum
        """
        album = self.get_object()
        serializer = self.get_serializer(album, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            album = serializer.save()
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        read_serializer = AlbumSerializer(album)
        return Response(read_serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        DELETE /albums/{id} - Eliminar álbum
        """
        album = self.get_object()
        album.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def album_songs(self, request, pk=None):
        """
        GET /albums/{album_id}/tracks - Obtener álbum con sus canciones
        """
        album = self.get_object()
        serializer = self.get_serializer(album)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Búsqueda de álbumes por título o artista
        """
        query = request.query_params.get('q', '')
        queryset = self.get_queryset()

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(artist__name__icontains=query)
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