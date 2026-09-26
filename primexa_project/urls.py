from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from exchange.seo_views import robots_txt
from exchange.sitemaps import (
    StaticViewSitemap,
    PublicVendorProfileSitemap,
    PublicExpertProfileSitemap,
    PublicOEMProfileSitemap,
)


sitemaps = {
    "static": StaticViewSitemap,
    "vendors": PublicVendorProfileSitemap,
    "experts": PublicExpertProfileSitemap,
    "oems": PublicOEMProfileSitemap,
}


urlpatterns = [

    path(
        "admin/",
        admin.site.urls,
    ),

    path("robots.txt", robots_txt, name="robots_txt"),

    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),

    path(
        "",
        include("exchange.public_urls"),
    ),

    path(
        "",
        include("users.urls"),
    ),

    path(
        "exchange/",
        include("exchange.urls"),
    ),

]
# ==============================================================
# DEVELOPMENT MEDIA FILES
# MEDIA FILES SERVING (DEVELOPMENT & PRODUCTION / CPANEL)
# ==============================================================

if settings.DEBUG:
from django.views.static import serve
from django.urls import re_path

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
urlpatterns += [
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]

