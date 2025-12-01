class UserFromHeaderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # El API Gateway pasa el user_id como string en el header
        user_id = request.headers.get('X-User-ID')

        if user_id and isinstance(user_id, str) and user_id.strip():
            # Limpiar y normalizar el user_id
            clean_user_id = user_id.strip()
            request.user = SimpleUser(clean_user_id)
        else:
            # Usuario anónimo
            request.user = AnonymousUser()

        return self.get_response(request)


class SimpleUser:
    """User mínimo compatible con Django auth"""

    def __init__(self, user_id):
        self.id = user_id
        self.is_authenticated = True
        self.is_active = True


class AnonymousUser:
    """Usuario no autenticado"""

    def __init__(self):
        self.id = None
        self.is_authenticated = False
        self.is_active = False