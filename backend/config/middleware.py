from urllib.parse import urlparse

from django.conf import settings


class ContentSecurityPolicyMiddleware:
    """Add Content-Security-Policy and Referrer-Policy headers to all responses."""

    def __init__(self, get_response):
        self.get_response = get_response
        r2_origin = self._get_r2_origin()
        vite_http, vite_ws = self._get_vite_dev_origins()
        self.csp = "; ".join([
            "default-src 'self'",
            f"img-src 'self' blob: data: {r2_origin}".strip(),
            f"script-src 'self' 'unsafe-inline' {vite_http}".strip(),
            f"style-src 'self' fonts.googleapis.com 'unsafe-inline' {vite_http}".strip(),
            "font-src fonts.gstatic.com",
            f"connect-src 'self' {vite_http} {vite_ws}".strip(),
            "frame-ancestors 'none'",
        ])

    def __call__(self, request):
        response = self.get_response(request)
        response['Content-Security-Policy'] = self.csp
        response['Referrer-Policy'] = 'same-origin'
        return response

    @staticmethod
    def _get_vite_dev_origins():
        """Vite dev server origins; empty unless dev_mode, so production CSP stays tight."""
        config = getattr(settings, 'DJANGO_VITE', {}).get('default', {})
        if not config.get('dev_mode'):
            return '', ''
        host = config.get('dev_server_host', 'localhost')
        port = config.get('dev_server_port', 5173)
        # ws:// is the HMR socket; without it connect-src blocks hot reload.
        return f'http://{host}:{port}', f'ws://{host}:{port}'

    @staticmethod
    def _get_r2_origin():
        endpoint = getattr(settings, 'OBJECT_STORAGE_ENDPOINT_URL', '')
        if endpoint:
            parsed = urlparse(endpoint)
            return f"{parsed.scheme}://{parsed.hostname}"
        return ''