from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Country
from .serializers import (
    CountrySerializer,
    CountryCreateSerializer,
    CountryUpdateSerializer
)


class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.prefetch_related('artists', 'record_labels')
    serializer_class = CountrySerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return CountryCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CountryUpdateSerializer
        return CountrySerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Filtros
        continent = self.request.query_params.get('continent')
        is_active = self.request.query_params.get('is_active')
        search = self.request.query_params.get('search')

        if continent:
            queryset = queryset.filter(continent=continent)

        if is_active is not None:
            if is_active.lower() == 'true':
                queryset = queryset.filter(is_active=True)
            elif is_active.lower() == 'false':
                queryset = queryset.filter(is_active=False)

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(iso_code__icontains=search) |
                Q(iso_code_3__icontains=search)
            )

        return queryset

    def list(self, request, *args, **kwargs):
        """
        Listar países - Puedes agregar paginación si lo necesitas
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Para tablas diccionario, a veces es mejor sin paginación
        # pero si tienes muchos países, puedes habilitarla:
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        Crear país
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            country = serializer.save()
        except serializer.ValidationError as e:
            # Manejar error de duplicado como 409 Conflict
            if 'iso_code' in e.detail or 'name' in e.detail:
                return Response(
                    {'error': 'Ya existe un país con este código ISO o nombre'},
                    status=status.HTTP_409_CONFLICT
                )
            raise e
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        read_serializer = CountrySerializer(country)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        """
        Obtener detalles de un país
        """
        country = self.get_object()
        serializer = self.get_serializer(country)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """
        Actualizar país
        """
        country = self.get_object()
        serializer = self.get_serializer(country, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        try:
            country = serializer.save()
        except serializer.ValidationError as e:
            # Manejar error de duplicado como 409 Conflict
            if 'iso_code' in e.detail or 'name' in e.detail:
                return Response(
                    {'error': 'Ya existe un país con este código ISO o nombre'},
                    status=status.HTTP_409_CONFLICT
                )
            raise e
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        read_serializer = CountrySerializer(country)
        return Response(read_serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Eliminar país
        """
        country = self.get_object()

        # Verificar si hay relaciones antes de eliminar
        if country.artists_count > 0 or country.record_labels_count > 0:
            return Response(
                {'error': 'No se puede eliminar el país porque tiene artistas o sellos discográficos asociados'},
                status=status.HTTP_400_BAD_REQUEST
            )

        country.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def artists(self, request, pk=None):
        """
        Obtener artistas de este país
        """
        country = self.get_object()

        # Importación diferida
        from artist.serializers import ArtistSerializer

        artists = country.artists.all()

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
    def record_labels(self, request, pk=None):
        """
        Obtener sellos discográficos de este país
        """
        country = self.get_object()

        # Importación diferida
        from record_label.serializers import RecordLabelSerializer

        record_labels = country.record_labels.all()

        page = self.paginate_queryset(record_labels)
        if page is not None:
            serializer = RecordLabelSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = RecordLabelSerializer(record_labels, many=True)
        return Response({
            'items': serializer.data,
            'total': record_labels.count()
        })

    @action(detail=False, methods=['get'])
    def continents(self, request):
        """
        Listar continentes disponibles
        """
        continents = Country.objects.filter(
            continent__isnull=False
        ).values_list(
            'continent', flat=True
        ).distinct()

        continent_choices = dict(Country._meta.get_field('continent').choices)

        continent_list = []
        for continent_code in continents:
            continent_list.append({
                'code': continent_code,
                'name': continent_choices.get(continent_code, continent_code),
                'countries_count': Country.objects.filter(continent=continent_code).count()
            })

        return Response(continent_list)