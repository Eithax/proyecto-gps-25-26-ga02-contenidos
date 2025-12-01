from rest_framework import permissions
import logging

logger = logging.getLogger(__name__)


class IsPlaylistOwner(permissions.BasePermission):
    """
    Verifica que el usuario autenticado sea el owner de la playlist
    Compara strings para el owner_id
    """

    def has_object_permission(self, request, view, obj):
        if not request.user or not hasattr(request.user, 'id'):
            return False

        # Comparación de strings (case-sensitive o insensitive según tu necesidad)
        return str(obj.owner_id) == str(request.user.id)


class IsAuthenticatedAndValidUser(permissions.BasePermission):
    """
    Verifica que el usuario esté autenticado y sea válido
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Verificar que tenemos un user_id válido
        if not hasattr(request.user, 'id') or not request.user.id:
            return False

        # Validar formato básico del user_id
        user_id = str(request.user.id)
        if not user_id.strip() or len(user_id) > 100:
            return False

        # Opcional: validar existencia en microservicio (puede ser costoso)
        # Solo para operaciones críticas
        if view.action in ['create', 'update', 'destroy']:
            from .services.user_service import UserService
            return UserService.validate_user_exists(user_id)

        return True