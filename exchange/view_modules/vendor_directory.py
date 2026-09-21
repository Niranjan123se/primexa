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
    """Deterministic discovery of manufacturing vendor profiles."""

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

    # Ensure all vendor profiles have a valid public_slug
    for vp in VendorProfile.objects.filter(Q(public_slug__isnull=True) | Q(public_slug="")):
        vp.save()

    profiles = VendorProfile.objects.all()

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
        )
    if filters["certification"]:
        profiles = profiles.filter(
            certification_records__certification_type=filters["certification"],
            certification_records__is_active=True,
        )
    if filters["industry"]:
        profiles = profiles.filter(
            industries_served__industry=filters["industry"],
            industries_served__is_active=True,
        )
    if filters["availability"] == "open_to_subcontract":
        profiles = profiles.filter(is_open_to_subcontract=True)
    if filters["verified"]:
        profiles = profiles.filter(is_verified=True)

    profiles = _public_vendor_queryset().filter(pk__in=profiles.distinct()).order_by(
        "user__company_name"
    )

    if not profiles.exists() and not any(filters.values()):
        profiles = VendorProfile.objects.select_related("user").all().order_by("user__company_name")

    selected_filter_count = sum(
        bool(filters[name])
        for name in (
            "q",
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
        profile.match_score = 100 if selected_filter_count else None

    from django.core.paginator import Paginator
    per_page_str = request.GET.get("per_page", "9")
    try:
        per_page = int(per_page_str)
        if per_page not in (6, 9, 12, 18, 36):
            per_page = 9
    except ValueError:
        per_page = 9

    paginator = Paginator(profiles, per_page)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    # Build GET parameters query string without page/per_page for pagination links
    query_params = request.GET.copy()
    if "page" in query_params:
        query_params.pop("page")
    querystring = query_params.urlencode()

    all_vps = VendorProfile.objects.all()

    return render(
        request,
        "exchange/vendor_directory.html",
        {
            "profiles": page_obj,
            "page_obj": page_obj,
            "per_page": per_page,
            "querystring": querystring,
            "total_count": paginator.count,
            "filters": filters,
            "canonical_url": request.build_absolute_uri(
                reverse("vendor_directory")
            ),
            "filter_options": {
                "cities": all_vps.exclude(city="").order_by("city").values_list(
                    "city", flat=True
                ).distinct(),
                "industrial_areas": all_vps.exclude(
                    industrial_area=""
                ).order_by("industrial_area").values_list(
                    "industrial_area", flat=True
                ).distinct(),
                "processes": VendorProcessCapability.PROCESS_CHOICES,
                "machine_types": VendorMachine.objects.filter(
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
    """Render a public vendor profile without procurement data."""

    profile = (
        _public_vendor_queryset()
        .filter(
            Q(public_slug=slug) | Q(user__username=slug) | Q(vendor_id_code=slug)
        )
        .first()
    )

    if profile is None:
        profile = (
            VendorProfile.objects.select_related("user")
            .filter(
                Q(public_slug=slug) | Q(user__username=slug) | Q(vendor_id_code=slug)
            )
            .first()
        )

    if profile is None:
        raise Http404("Vendor profile not found.")

    is_staff = request.user.is_authenticated and (request.user.is_superuser or getattr(request.user, "role", "") == "ENGINEER")
    is_owner = request.user.is_authenticated and request.user == profile.user
    is_authenticated = request.user.is_authenticated
    is_public = (profile.is_public_profile and profile.is_public_profile_approved) or profile.is_verified

    if not (is_public or is_authenticated or is_staff or is_owner):
        raise Http404("Vendor profile not found.")

    vendor_slug = profile.public_slug or profile.user.username
    canonical_url = request.build_absolute_uri(
        reverse("public_vendor_profile", kwargs={"slug": vendor_slug})
    )
    company_name = profile.user.company_name or profile.user.username
    city_str = profile.city or "India"
    location_str = f"{profile.industrial_area}, {profile.city}, {profile.state}".strip(", ")

    processes_list = [p.get_process_type_display() for p in profile.process_capabilities.all()]
    machine_names = [m.machine_name for m in profile.machines.all()]
    capabilities_summary = ", ".join(processes_list[:3] + machine_names[:2]) or "CNC machining and precision manufacturing"

    meta_title = f"{company_name} - {capabilities_summary} in {city_str} | Primexa Network"

    description = profile.public_description.strip() or (
        f"{company_name} provides {capabilities_summary} services in {location_str or city_str}. Verified manufacturing vendor on Primexa Exchange."
    )
    meta_description = Truncator(description).chars(155)

    from django.db.models import Avg
    reviews = profile.reviews.select_related("reviewer").filter(is_approved=True)
    avg_rating = reviews.aggregate(Avg("rating"))["rating__avg"]
    avg_rating = round(avg_rating, 1) if avg_rating else None

    address = {
        "@type": "PostalAddress",
        "addressLocality": profile.city,
        "addressRegion": profile.state,
        "postalCode": profile.pin_code,
        "addressCountry": profile.country or "IN",
    }
    organization_schema = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": company_name,
        "url": canonical_url,
        "description": description,
        "address": address,
        "knowsAbout": processes_list + machine_names,
        "areaServed": location_str or city_str,
    }
    if avg_rating and reviews.count() > 0:
        organization_schema["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": str(avg_rating),
            "reviewCount": str(reviews.count()),
            "bestRating": "5",
            "worstRating": "1",
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
            "reviews": reviews,
            "avg_rating": avg_rating,
            "review_count": reviews.count(),
            "canonical_url": canonical_url,
            "meta_title": meta_title,
            "meta_description": meta_description,
            "organization_schema": json.dumps(organization_schema).replace("<", r"\u003c"),
        },
    )
