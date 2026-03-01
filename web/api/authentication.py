import secrets

from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission


class ApiKeyAuthentication(BaseAuthentication):
    """Custom authentication using X-Api-Key header."""

    def authenticate(self, request):
        api_key = request.headers.get('X-Api-Key')
        if not api_key:
            return None

        if not secrets.compare_digest(api_key, settings.API_KEY):
            raise AuthenticationFailed('Invalid API key')

        return None, api_key


class RequireApiKey(BasePermission):
    """Permission class that requires API key authentication."""

    def has_permission(self, request, view):
        return request.auth is not None
