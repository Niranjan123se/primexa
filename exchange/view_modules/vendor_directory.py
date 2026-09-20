import json

from django.db.models import Prefetch, Q
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse
from django.utils.text import Truncator

from users.models import VendorProfile

from ..models import (
    VendorCertification,
    VendorIndustry,
    VendorMachine,
    VendorMaterial,
    VendorProcessCapability,
    VendorQualityInstrument,
    VendorServiceCategory,
    VendorShopPhoto,
)


def public_home(request):
    """Public Primexa entry point for vendor-network discovery."""
    public_profiles = VendorProfile.objects.filter(
        is_public_profile=True,
        is_public_profile_approved=True,
        public_slug__isnull=False,
    ).exclude(public_slug="")

    machine_types = (
        VendorMachine.objects.filter(profile__in=public_profiles, is_active=True)
        .exclude(machine_type="")
        .order_by("machine_type")
        .values_list("machine_type", flat=True)
        .distinct()
    )

    return render(
        request,
        "exchange/public_home.html",
        {
            "processes": VendorProcessCapability.PROCESS_CHOICES,
            "machine_types": machine_types,
        },
    )


def _public_vendor_queryset():
    """Return public vendor profiles with only public discovery data prefetched."""
    return VendorProfile.objects.select_related("user").prefetch_related(
        Prefetch(
            "process_capabilities",
            queryset=VendorProcessCapability.objects.filter(is_active=True),
        ),
        Prefetch(
            "machines",
            queryset=VendorMachine.objects.filter(is_active=True).prefetch_related(
                "processes"
            ),
        ),
        Prefetch(
            "materials",
            queryset=VendorMaterial.objects.filter(is_active=True, is_public=True),
        ),
        Prefetch(
            "certification_records",
            queryset=VendorCertification.objects.filter(
                is_active=True,
                is_public=True,
            ),
        ),
        Prefetch(
            "quality_instrument_records",
            queryset=VendorQualityInstrument.objects.filter(
                is_active=True,
                is_public=True,
            ),
        ),
        Prefetch(
            "industries_served",
            queryset=VendorIndustry.objects.filter(is_active=True, is_public=True),
        ),
        Prefetch(
            "service_categories",
            queryset=VendorServiceCategory.objects.filter(is_active=True),
        ),
        Prefetch(
            "shop_photos",
            queryset=VendorShopPhoto.objects.filter(
                is_public=True,
                is_approved=True,
            ),
        ),
    )


def vendor_directory(request):
    """Deterministic discovery of approved public vendor profiles."""

    filters = {
        "q": request.GET.get("q", "").strip(),
        "city": request.GET.get("city", "").strip(),
        "industrial_area": request.GET.get("industrial_area", "").strip(),
        "process": request.GET.get("process", "").strip(),
        "machine_type": request.GET.get("machine_type", "").strip(),
        "material": request.GET.get("material", "").strip(),
        "certification": request.GET.get("certification", "").strip(),
        "industry": request.GET.get("industry", "").strip(),
        "availability": request.GET.get("availability", "").strip(),
        "verified": request.GET.get("verified", "") == "1",
    }

    profiles = VendorProfile.objects.filter(
        is_public_profile=True,
        is_public_profile_approved=True,
        public_slug__isnull=False,
    ).exclude(public_slug="")

    if filters["q"]:
        profiles = profiles.filter(
            Q(user__company_name__icontains=filters["q"])
            | Q(public_description__icontains=filters["q"])
            | Q(city__icontains=filters["q"])
            | Q(industrial_area__icontains=filters["q"])
            | Q(machines__machine_name__icontains=filters["q"])
            | Q(machines__manufacturer__icontains=filters["q"])
        )
    if filters["city"]:
        profiles = profiles.filter(city__iexact=filters["city"])
    if filters["industrial_area"]:
        profiles = profiles.filter(
            industrial_area__iexact=filters["industrial_area"]
        )
    if filters["process"]:
        profiles = profiles.filter(
            process_capabilities__process_type=filters["process"],
            process_capabilities__is_active=True,
        )
    if filters["machine_type"]:
        profiles = profiles.filter(
            machines__machine_type__iexact=filters["machine_type"],
            machines__is_active=True,
        )
    if filters["material"]:
        profiles = profiles.filter(
            materials__material_type=filters["material"],
            materials__is_active=True,
            materials__is_public=True,
        )
    if filters["certification"]:
        profiles = profiles.filter(
            certification_records__certification_type=filters["certification"],
            certification_records__is_active=True,
            certification_records__is_public=True,
        )
    if filters["industry"]:
        profiles = profiles.filter(
            industries_served__industry=filters["industry"],
            industries_served__is_active=True,
            industries_served__is_public=True,
        )
    if filters["availability"] == "open_to_subcontract":
        profiles = profiles.filter(is_open_to_subcontract=True)
    if filters["verified"]:
        profiles = profiles.filter(is_verified=True)

    profiles = _public_vendor_queryset().filter(pk__in=profiles.distinct()).order_by(
        "user__company_name"
    )

    selected_filter_count = sum(
        bool(filters[name])
        for name in (
            "city",
            "industrial_area",
            "process",
            "machine_type",
            "material",
            "certification",
            "industry",
            "availability",
            "verified",
        )
    )
    for profile in profiles:
        # Every result satisfies each active deterministic filter. This value is
        # intentionally a filter-match percentage, not an AI recommendation.
        profile.match_score = 100 if selected_filter_count else None

    public_profiles = VendorProfile.objects.filter(
        is_public_profile=True,
        is_public_profile_approved=True,
        public_slug__isnull=False,
    ).exclude(public_slug="")

    return render(
        request,
        "exchange/vendor_directory.html",
        {
            "profiles": profiles,
            "filters": filters,
            "canonical_url": request.build_absolute_uri(
                reverse("vendor_directory")
            ),
            "filter_options": {
                "cities": public_profiles.exclude(city="").order_by("city").values_list(
                    "city", flat=True
                ).distinct(),
                "industrial_areas": public_profiles.exclude(
                    industrial_area=""
                ).order_by("industrial_area").values_list(
                    "industrial_area", flat=True
                ).distinct(),
                "processes": VendorProcessCapability.PROCESS_CHOICES,
                "machine_types": VendorMachine.objects.filter(
                    profile__in=public_profiles,
                    is_active=True,
                ).exclude(machine_type="").order_by("machine_type").values_list(
                    "machine_type", flat=True
                ).distinct(),
                "materials": VendorMaterial.MATERIAL_CHOICES,
                "certifications": VendorCertification.CERTIFICATION_CHOICES,
                "industries": VendorIndustry.INDUSTRY_CHOICES,
            },
            "selected_filter_count": selected_filter_count,
        },
    )


def public_vendor_profile(request, slug):
    """Render an approved public vendor profile without procurement data."""

    profile = (
        _public_vendor_queryset()
        .filter(
            public_slug=slug,
            is_public_profile=True,
            is_public_profile_approved=True,
        )
        .first()
    )

    if profile is None:
        raise Http404("Vendor profile not found.")

    canonical_url = request.build_absolute_uri(
        reverse("public_vendor_profile", kwargs={"slug": profile.public_slug})
    )
    company_name = profile.user.company_name
    description = profile.public_description.strip() or (
        f"{company_name} is a verified manufacturing vendor in the Primexa network."
    )
    meta_description = Truncator(description).chars(155)

    address = {
        "@type": "PostalAddress",
        "addressLocality": profile.city,
        "addressRegion": profile.state,
        "postalCode": profile.pin_code,
        "addressCountry": profile.country,
    }
    organization_schema = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": company_name,
        "url": canonical_url,
        "description": description,
        "address": address,
    }
    if profile.public_enquiry_email:
        organization_schema["email"] = profile.public_enquiry_email
    if profile.public_enquiry_phone:
        organization_schema["telephone"] = profile.public_enquiry_phone

    return render(
        request,
        "exchange/vendor_public_profile.html",
        {
            "profile": profile,
            "canonical_url": canonical_url,
            "meta_title": f"{company_name} | Manufacturing Vendor | Primexa",
            "meta_description": meta_description,
            "organization_schema": json.dumps(organization_schema).replace("<", r"\u003c"),
        },
    )
