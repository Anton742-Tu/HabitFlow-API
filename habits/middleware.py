class SecurityHeadersMiddleware:
    """Middleware для добавления security headers"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Security headers
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["X-XSS-Protection"] = "1; mode=block"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # CORS headers (дублируем для гарантии)
        if "HTTP_ORIGIN" in request.META:
            origin = request.META["HTTP_ORIGIN"]
            # Проверяем что origin разрешен
            from django.conf import settings

            if (
                origin in settings.CORS_ALLOWED_ORIGINS
                or settings.CORS_ALLOW_ALL_ORIGINS
            ):
                response["Access-Control-Allow-Origin"] = origin
                response["Access-Control-Allow-Credentials"] = "true"

        return response
