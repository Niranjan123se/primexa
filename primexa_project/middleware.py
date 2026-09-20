class AuthenticatedPageNoIndexMiddleware:
    """Prevent crawlers from indexing authenticated application pages."""

    public_prefixes = ("/vendors/", "/robots.txt", "/sitemap.xml")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if (
            request.user.is_authenticated
            and not request.path.startswith(self.public_prefixes)
        ):
            response["X-Robots-Tag"] = "noindex, nofollow, noarchive"
        return response
