from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import RecordLabel
from .serializers import (
    RecordLabelSerializer,
    RecordLabelCreateSerializer,
    RecordLabelUpdateSerializer
)


class RecordLabelViewSet(viewsets.ModelViewSet):
    queryset = RecordLabel.objects.select_related('country').prefetch_related('artists')
    serializer_class = RecordLabelSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return RecordLabelCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return RecordLabelUpdateSerializer
        return RecordLabelSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset

    def list(self, request, *args, **kwargs):
        """
        GET /labels - Listar todas las discográficas
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Paginación
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """
        GET /labels/{label_id} - Obtener detalles de una discográfica
        """
        record_label = self.get_object()
        serializer = self.get_serializer(record_label)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        POST /labels - Crear discográfica
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            record_label = serializer.save()
        except serializer.ValidationError as e:
            # Manejar error de duplicado como 409 Conflict
            if 'name' in e.detail and 'Ya existe' in str(e.detail['name']):
                return Response(
                    {'error': 'Ya existe un sello discográfico con este nombre'},
                    status=status.HTTP_409_CONFLICT
                )
            raise e
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        read_serializer = RecordLabelSerializer(record_label)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        """
        PATCH /labels/{label_id} - Actualizar discográfica
        """
        record_label = self.get_object()
        serializer = self.get_serializer(record_label, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            record_label = serializer.save()
        except serializer.ValidationError as e:
            # Manejar error de duplicado como 409 Conflict
            if 'name' in e.detail and 'Ya existe' in str(e.detail['name']):
                return Response(
                    {'error': 'Ya existe un sello discográfico con este nombre'},
                    status=status.HTTP_409_CONFLICT
                )
            raise e
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        read_serializer = RecordLabelSerializer(record_label)
        return Response(read_serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        DELETE /labels/{label_id} - Eliminar discográfica
        """
        record_label = self.get_object()

        # Verificar si hay artistas asociados antes de eliminar
        if record_label.artists_count > 0:
            return Response(
                {'error': 'No se puede eliminar el sello porque tiene artistas asociados'},
                status=status.HTTP_400_BAD_REQUEST
            )

        record_label.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def artists(self, request, pk=None):
        """
        GET /labels/{label_id}/artists - Obtener artistas del sello
        """
        record_label = self.get_object()
        artists = record_label.artists.all()

        from artist.serializers import ArtistSerializer

        page = self.paginate_queryset(artists)
        if page is not None:
            serializer = ArtistSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ArtistSerializer(artists, many=True)
        return Response({
            'items': serializer.data,
            'total': artists.count()
        })

    @action(detail=True, methods=['get'])
    def albums(self, request, pk=None):
        """
        GET /labels/{label_id}/albums - Obtener álbumes del sello
        """
        record_label = self.get_object()
        from album.models import Album
        from album.serializers import AlbumSerializer

        albums = Album.objects.filter(artist__label_id=record_label)

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
    def search(self, request):
        """
        Búsqueda de sellos discográficos por nombre
        """
        query = request.query_params.get('q', '')
        queryset = self.get_queryset()

        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(country__name__icontains=query)
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