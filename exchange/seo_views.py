from django.http import HttpResponse
from django.urls import reverse


def robots_txt(request):
    sitemap_url = request.build_absolute_uri(reverse("sitemap"))
    content = "\n".join(
        [
            "User-agent: *",
            "Allow: /vendors/",
            "Allow: /robots.txt",
            "Allow: /sitemap.xml",
            "Disallow: /admin/",
            "Disallow: /exchange/",
            "Disallow: /profile/",
            "Disallow: /login/",
            "Disallow: /logout/",
            "Disallow: /register/",
            "Disallow: /password-reset/",
            f"Sitemap: {sitemap_url}",
            "",
        ]
    )
    return HttpResponse(content, content_type="text/plain")
