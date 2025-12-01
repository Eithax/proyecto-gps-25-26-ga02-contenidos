import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class UserService:
    @staticmethod
    def validate_user_exists(user_id):
        """
        Valida que el usuario exista en el microservicio de usuarios
        user_id es un string que puede tener cualquier formato
        """
        if not user_id or not isinstance(user_id, str):
            return False

        try:
            response = requests.get(
                f"{settings.USER_SERVICE_URL}/api/v1/users/{user_id}",
                headers={
                    'Authorization': f'Bearer {settings.INTERNAL_API_TOKEN}',
                    'Content-Type': 'application/json'
                },
                timeout=settings.REQUESTS_TIMEOUT
            )

            # Dependiendo de cómo responda tu API de usuarios
            if response.status_code == 200:
                return True
            elif response.status_code == 404:
                logger.warning(f"Usuario no encontrado: {user_id}")
                return False
            else:
                logger.error(f"Error validando usuario {user_id}: {response.status_code}")
                # En producción, decide si fallar o continuar
                return settings.DEBUG  # En dev=True, en prod=False

        except requests.RequestException as e:
            logger.error(f"Error de conexión validando usuario {user_id}: {str(e)}")
            # Dependiendo de tu tolerancia a fallos
            return settings.DEBUG

    @staticmethod
    def get_user_display_info(user_id):
        """Obtiene información del usuario para mostrar"""
        if not user_id:
            return {'username': 'usuario_desconocido', 'display_name': 'Usuario'}

        try:
            response = requests.get(
                f"{settings.USER_SERVICE_URL}/api/v1/users/{user_id}/profile",
                headers={
                    'Authorization': f'Bearer {settings.INTERNAL_API_TOKEN}',
                    'Content-Type': 'application/json'
                },
                timeout=settings.REQUESTS_TIMEOUT
            )

            if response.status_code == 200:
                user_data = response.json()
                # Normalizar la respuesta según la estructura de tu API
                return {
                    'username': user_data.get('username', f'user_{user_id}'),
                    'display_name': user_data.get('display_name', 'Usuario'),
                    'avatar_url': user_data.get('avatar_url'),
                    'premium': user_data.get('is_premium', False)
                }

        except requests.RequestException as e:
            logger.error(f"Error obteniendo info usuario {user_id}: {str(e)}")

        # Fallback si hay error
        return {
            'username': f'user_{user_id}',
            'display_name': 'Usuario',
            'avatar_url': None,
            'premium': False
        }