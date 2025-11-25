from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from playlist.models import Playlist
from playlist.permissions import IsAuthenticatedAndValidUser, IsPlaylistOwner
from playlist.serializers import PlaylistSerializer


class PlaylistViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedAndValidUser, IsPlaylistOwner]
    serializer_class = PlaylistSerializer

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