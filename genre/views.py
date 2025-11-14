from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Genre
from .serializers import (
    GenreSerializer,
    GenreCreateSerializer,
    GenreUpdateSerializer
)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.select_related('parent_genre').prefetch_related('tracks', 'albums')
    serializer_class = GenreSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return GenreCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return GenreUpdateSerializer
        return GenreSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtrar por si es subgénero o no
        is_subgenre = self.request.query_params.get('is_subgenre')
        parent_genre_id = self.request.query_params.get('parent_genre_id')

        if is_subgenre is not None:
            if is_subgenre.lower() == 'true':
                queryset = queryset.filter(parent_genre__isnull=False)
            elif is_subgenre.lower() == 'false':
                queryset = queryset.filter(parent_genre__isnull=True)

        if parent_genre_id:
            queryset = queryset.filter(parent_genre_id=parent_genre_id)

        return queryset

    def list(self, request, *args, **kwargs):
        """
        GET /genres - Listar géneros musicales
        """
        queryset = self.filter_queryset(self.get_queryset())

        # No paginamos para mantener estructura jerárquica
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        POST /genres - Crear género musical
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            genre = serializer.save()
        except serializer.ValidationError as e:
            # Manejar error de duplicado como 409 Conflict
            if 'name' in e.detail and 'Ya existe' in str(e.detail['name']):
                return Response(
                    {'error': 'Ya existe un género con este nombre'},
                    status=status.HTTP_409_CONFLICT
                )
            raise e
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        read_serializer = GenreSerializer(genre)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        """
        GET /genres/{genre_id} - Obtener detalles de un género
        """
        genre = self.get_object()
        serializer = self.get_serializer(genre)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """
        PATCH /genres/{genre_id} - Actualizar género musical
        """
        genre = self.get_object()
        serializer = self.get_serializer(genre, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            genre = serializer.save()
        except serializer.ValidationError as e:
            # Manejar error de duplicado como 409 Conflict
            if 'name' in e.detail and 'Ya existe' in str(e.detail['name']):
                return Response(
                    {'error': 'Ya existe un género con este nombre'},
                    status=status.HTTP_409_CONFLICT
                )
            raise e
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        read_serializer = GenreSerializer(genre)
        return Response(read_serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        DELETE /genres/{genre_id} - Eliminar género musical
        """
        genre = self.get_object()

        # Verificar si hay relaciones antes de eliminar
        if genre.tracks_count > 0 or genre.albums_count > 0:
            return Response(
                {'error': 'No se puede eliminar el género porque tiene pistas o álbumes asociados'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verificar si tiene subgéneros
        if genre.subgenres.exists():
            return Response(
                {'error': 'No se puede eliminar el género porque tiene subgéneros asociados'},
                status=status.HTTP_400_BAD_REQUEST
            )

        genre.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def subgenres(self, request, pk=None):
        """
        GET /genres/{genre_id}/subgenres - Obtener subgéneros
        """
        genre = self.get_object()
        subgenres = genre.subgenres.all()

        serializer = self.get_serializer(subgenres, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def tracks(self, request, pk=None):
        """
        GET /genres/{genre_id}/tracks - Obtener pistas del género
        """
        genre = self.get_object()

        # Importación diferida para evitar circularidad
        from track.serializers import TrackSerializer

        tracks = genre.tracks.all()

        page = self.paginate_queryset(tracks)
        if page is not None:
            serializer = TrackSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = TrackSerializer(tracks, many=True)
        return Response({
            'items': serializer.data,
            'total': tracks.count()
        })

    @action(detail=True, methods=['get'])
    def albums(self, request, pk=None):
        """
        GET /genres/{genre_id}/albums - Obtener álbumes del género
        """
        genre = self.get_object()

        # Importación diferida para evitar circularidad
        from album.serializers import AlbumSerializer

        albums = genre.albums.all()

        page = self.paginate_queryset(albums)
        if page is not None:
            serializer = AlbumSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = AlbumSerializer(albums, many=True)
        return Response({
            'items': serializer.data,
            'total': albums.count()
        })

    @action(detail=False, methods=['get'])
    def hierarchy(self, request):
        """
        GET /genres/hierarchy - Obtener estructura jerárquica completa
        """
        main_genres = Genre.objects.filter(parent_genre__isnull=True)
        hierarchy = []

        def build_hierarchy(genre):
            return {
                'genre': GenreSerializer(genre).data,
                'subgenres': [build_hierarchy(sg) for sg in genre.subgenres.all()]
            }

        for genre in main_genres:
            hierarchy.append(build_hierarchy(genre))

        return Response(hierarchy)