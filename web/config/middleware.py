from urllib.parse import urlparse

from django.conf import settings


class ContentSecurityPolicyMiddleware:
    """Add Content-Security-Policy header to all responses."""

    def __init__(self, get_response):
        self.get_response = get_response
        r2_origin = self._get_r2_origin()
        self.csp = "; ".join([
            "default-src 'self'",
            f"img-src 'self' blob: data: {r2_origin}",
            "script-src 'self' cdn.jsdelivr.net 'unsafe-inline' 'unsafe-eval'",
            "style-src 'self' fonts.googleapis.com 'unsafe-inline'",
            "font-src fonts.gstatic.com",
            "connect-src 'self'",
            "frame-ancestors 'none'",
        ])

    def __call__(self, request):
        response = self.get_response(request)
        response['Content-Security-Policy'] = self.csp
        return response

    @staticmethod
    def _get_r2_origin():
        endpoint = getattr(settings, 'OBJECT_STORAGE_ENDPOINT_URL', '')
        if endpoint:
            parsed = urlparse(endpoint)
            return f"{parsed.scheme}://{parsed.hostname}"
        return ''