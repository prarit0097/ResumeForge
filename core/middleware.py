"""Privacy headers — resumes contain PII, so keep them out of search engines
and avoid leaking the secret edit-token URL to external sites via the Referer
header.

We use ``same-origin`` (not ``no-referrer``): the token URL is still never sent
to external origins (Google Fonts, etc.), but same-origin requests keep a valid
Origin header. ``no-referrer`` makes Chrome send ``Origin: null`` on HTML form
POSTs, which Django's CSRF check then rejects (breaks uploads and form buttons).
"""


# Paths that contain personal resume data (or its secret token) must never be
# indexed. Public marketing pages (landing, the upload/enhance intro) SHOULD be
# indexable so the site can be found and traffic measured.
_PII_PREFIXES = ("/r/", "/drafts")


class PrivacyHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith(_PII_PREFIXES):
            response.setdefault("X-Robots-Tag", "noindex, nofollow")
        # same-origin keeps the secret ?t= token URL off external sites (it is
        # never sent cross-origin) while keeping CSRF working on form POSTs.
        response.setdefault("Referrer-Policy", "same-origin")
        return response
