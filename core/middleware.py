"""Privacy headers — resumes contain PII, so keep them out of search engines
and avoid leaking the secret edit-token URL via the Referer header."""


class PrivacyHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault("X-Robots-Tag", "noindex, nofollow")
        response.setdefault("Referrer-Policy", "no-referrer")
        return response
