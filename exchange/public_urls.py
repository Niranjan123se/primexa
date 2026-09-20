from django.urls import path

from .view_modules.vendor_directory import (
    public_home,
    public_vendor_profile,
    vendor_directory,
)


urlpatterns = [
    path("", public_home, name="public_home"),
    path(
        "vendors/",
        vendor_directory,
        name="vendor_directory",
    ),
    path(
        "vendors/<slug:slug>/",
        public_vendor_profile,
        name="public_vendor_profile",
    ),
]
