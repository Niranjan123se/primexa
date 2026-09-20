from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from users.models import VendorProfile


class PublicVendorProfileSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return VendorProfile.objects.filter(
            is_public_profile=True,
            is_public_profile_approved=True,
            public_slug__isnull=False,
        ).exclude(public_slug="").order_by("public_slug")

    def location(self, profile):
        return reverse("public_vendor_profile", kwargs={"slug": profile.public_slug})
