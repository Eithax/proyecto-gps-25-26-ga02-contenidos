from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from playlist.models import Playlist
from playlist.permissions import IsAuthenticatedAndValidUser, IsPlaylistOwner
from playlist.serializers import PlaylistSerializer


class PlaylistViewSet(viewsets.ModelViewSet):
    serializer_class = PlaylistSerializer

    def get_permissions(self):
        # === ENDPOINTS PÚBLICOS ===
        if self.action in ['public_tracks', 'discover']:
            return []  # No requiere autenticación

        # === ACCIONES QUE REQUIEREN QUE EL USUARIO SEA EL DUEÑO ===
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy',
                           'tracks', 'add_track', 'remove_track',
                           'move_track', 'clear_tracks', 'stats']:
            return [IsPlaylistOwner()]

        # === TODAS LAS DEMÁS EXIGEN QUE EL USUARIO ESTÉ AUTENTICADO ===
        return [IsAuthenticatedAndValidUser()]

    def get_queryset(self):
        # Filtrar por el user_id (string) del usuario autenticado
        return Playlist.objects.filter(owner_id=str(self.request.user.id))

    def get_serializer_class(self):
        if self.action == 'create':
            from .serializers import PlaylistCreateSerializer
            return PlaylistCreateSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        # Asignar el owner_id desde el usuario autenticado (string)
        serializer.save(owner_id=str(self.request.user.id))

    @action(detail=False, methods=['get'])
    def my_playlists(self, request):
        """Listar playlists del usuario actual"""
        playlists = self.get_queryset()
        page = self.paginate_queryset(playlists)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(playlists, many=True)
        return Response(serializer.data)

    # === ENDPOINTS PARA GESTIÓN DE TRACKS ===

    @action(detail=True, methods=['get'])
    def tracks(self, request, pk=None):
        """Obtener todos los tracks de una playlist ordenados por posición"""
        playlist = self.get_object()
        playlist_tracks = playlist.playlist_tracks.select_related(
            'track', 'track__artist', 'track__album'
        ).order_by('position')

        from .serializers import PlaylistTrackSerializer
        serializer = PlaylistTrackSerializer(playlist_tracks, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_track(self, request, pk=None):
        """Añadir un track a la playlist"""
        playlist = self.get_object()
        track_id = request.data.get('track_id')
        position = request.data.get('position', 0)

        if not track_id:
            return Response(
                {'error': 'El track_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from track.models import Track
            track = Track.objects.get(id=track_id)
        except Track.DoesNotExist:
            return Response(
                {'error': 'Track no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verificar si el track ya está en la playlist
        if playlist.contains_track(track):
            return Response(
                {'error': 'El track ya está en la playlist'},
                status=status.HTTP_409_CONFLICT
            )

        # Añadir el track
        playlist_track, created = playlist.add_track(track, position)

        from .serializers import PlaylistTrackSerializer
        serializer = PlaylistTrackSerializer(playlist_track)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'])
    def remove_track(self, request, pk=None):
        """Eliminar un track de la playlist"""
        playlist = self.get_object()
        track_id = request.data.get('track_id') or request.query_params.get('track_id')

        if not track_id:
            return Response(
                {'error': 'El track_id es requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from track.models import Track
            track = Track.objects.get(id=track_id)
        except Track.DoesNotExist:
            return Response(
                {'error': 'Track no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Eliminar el track
        removed = playlist.remove_track(track)

        if removed:
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {'error': 'El track no está en la playlist'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def move_track(self, request, pk=None):
        """Mover un track a una nueva posición en la playlist"""
        playlist = self.get_object()
        track_id = request.data.get('track_id')
        new_position = request.data.get('new_position')

        if not track_id or new_position is None:
            return Response(
                {'error': 'track_id y new_position son requeridos'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            new_position = int(new_position)
            if new_position < 1:
                return Response(
                    {'error': 'La posición debe ser mayor a 0'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (TypeError, ValueError):
            return Response(
                {'error': 'new_position debe ser un número válido'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from track.models import Track
            track = Track.objects.get(id=track_id)
        except Track.DoesNotExist:
            return Response(
                {'error': 'Track no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Mover el track
        success = playlist.move_track(track, new_position)

        if success:
            return Response({'message': 'Track movido correctamente'})
        else:
            return Response(
                {'error': 'El track no está en la playlist'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['delete'])
    def clear_tracks(self, request, pk=None):
        """Eliminar todos los tracks de la playlist"""
        playlist = self.get_object()

        deleted_count = playlist.clear_tracks()
        return Response({
            'message': f'Se eliminaron {deleted_count[0]} tracks de la playlist'
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Obtener estadísticas de la playlist"""
        playlist = self.get_object()

        stats = {
            'tracks_count': playlist.tracks_count,
            'total_duration_sec': playlist.total_duration,
            'total_duration_formatted': playlist.total_duration_formatted,
            'is_public': playlist.is_public,
            'created_at': playlist.created_at,
            'updated_at': playlist.updated_at
        }

        return Response(stats)

    # === ENDPOINTS PÚBLICOS (solo para playlists públicas) ===

    @action(detail=True, methods=['get'], permission_classes=[])
    def public_tracks(self, request, pk=None):
        """Obtener tracks de una playlist pública (sin autenticación requerida)"""
        playlist = get_object_or_404(Playlist, id=pk, is_public=True)

        playlist_tracks = playlist.playlist_tracks.select_related(
            'track', 'track__artist', 'track__album'
        ).order_by('position')

        from .serializers import PlaylistTrackSerializer
        serializer = PlaylistTrackSerializer(playlist_tracks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[])
    def discover(self, request):
        """Descubrir playlists públicas"""
        query = request.query_params.get('q', '')

        if query:
            playlists = Playlist.get_public_playlists().filter(
                models.Q(title__icontains=query) |
                models.Q(description__icontains=query)
            )
        else:
            playlists = Playlist.get_public_playlists()

        page = self.paginate_queryset(playlists)
        if page is not None:
            from .serializers import PlaylistPublicSerializer
            serializer = PlaylistPublicSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        from .serializers import PlaylistPublicSerializer
        serializer = PlaylistPublicSerializer(playlists, many=True)
        return Response(serializer.data)