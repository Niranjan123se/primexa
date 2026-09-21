from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.db.models import Q

from users.models import VendorProfile, ExpertProfile, OEMProfile


class StaticViewSitemap(Sitemap):
    priority = 0.9
    changefreq = "daily"

    def items(self):
        return ["public_home", "vendor_directory", "expert_directory", "request_service"]

    def location(self, item):
        return reverse(item)


class PublicVendorProfileSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        for vp in VendorProfile.objects.filter(Q(public_slug__isnull=True) | Q(public_slug="")):
            vp.save()
        return VendorProfile.objects.filter(
            is_public_profile_approved=True,
        ).exclude(Q(public_slug__isnull=True) | Q(public_slug="")).order_by("user__company_name")

    def location(self, profile):
        slug = profile.public_slug or profile.user.username
        return reverse("public_vendor_profile", kwargs={"slug": slug})


class PublicExpertProfileSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return ExpertProfile.objects.filter(is_public_profile=True).exclude(Q(slug__isnull=True) | Q(slug="")).order_by("slug")

    def location(self, profile):
        return reverse("public_expert_profile", kwargs={"slug": profile.slug})


class PublicOEMProfileSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return OEMProfile.objects.filter(is_approved=True).exclude(Q(slug__isnull=True) | Q(slug="")).order_by("slug")

    def location(self, profile):
        return reverse("public_oem_profile", kwargs={"slug": profile.slug})
