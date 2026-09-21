from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from users.models import OEMProfile, VendorProfile, ExpertProfile


@login_required
def approve_expert(request, company_slug):
    """
    Approve an Expert profile by slug.
    Sets is_verified and is_public_profile to True.
    """
    if not (request.user.is_superuser or request.user.role == "ENGINEER"):
        return HttpResponseForbidden("Security Block: Primexa staff engineer access required.")

    expert_profile = get_object_or_404(ExpertProfile.objects.select_related("user"), slug=company_slug)
    expert_profile.is_verified = True
    expert_profile.is_public_profile = True
    expert_profile.save(update_fields=["is_verified", "is_public_profile"])

    name = expert_profile.user.get_full_name() or expert_profile.user.company_name or expert_profile.user.username
    messages.success(request, f"Expert '{name}' (Slug: {company_slug}) has been approved successfully!")
    return redirect("engineer_dashboard")


@login_required
def approve_vendor(request, company_slug):
    """
    Approve a vendor profile by business name slug, username, or vendor ID code.
    Sets is_verified, is_public_profile, and is_public_profile_approved to True.
    """
    if not (request.user.is_superuser or request.user.role == "ENGINEER"):
        return HttpResponseForbidden("Security Block: Primexa staff engineer access required.")

    from django.db.models import Q
    from django.http import Http404

    vendor_profile = (
        VendorProfile.objects.select_related("user")
        .filter(
            Q(public_slug=company_slug)
            | Q(user__username=company_slug)
            | Q(vendor_id_code=company_slug)
        )
        .first()
    )
    if not vendor_profile:
        raise Http404("Vendor profile not found for approval.")

    vendor_profile.is_verified = True
    vendor_profile.is_public_profile = True
    vendor_profile.is_public_profile_approved = True
    vendor_profile.save(update_fields=["is_verified", "is_public_profile", "is_public_profile_approved"])

    company_name = vendor_profile.user.company_name or vendor_profile.user.username
    messages.success(request, f"Vendor business '{company_name}' has been approved successfully!")
    return redirect("engineer_dashboard")


@login_required
def approve_oem(request, company_slug):
    """
    Approve an OEM profile by business name slug.
    Sets is_verified and is_approved to True.
    """
    if not (request.user.is_superuser or request.user.role == "ENGINEER"):
        return HttpResponseForbidden("Security Block: Primexa staff engineer access required.")

    oem_profile = get_object_or_404(OEMProfile.objects.select_related("user"), slug=company_slug)
    oem_profile.is_verified = True
    oem_profile.is_approved = True
    oem_profile.save(update_fields=["is_verified", "is_approved"])

    company_name = oem_profile.user.company_name or oem_profile.user.username
    messages.success(request, f"OEM business '{company_name}' (Slug: {company_slug}) has been approved successfully!")
    return redirect("engineer_dashboard")


def public_oem_profile(request, slug):
    """
    Display public/internal OEM profile details by business name slug.
    """
    from django.http import Http404
    oem_profile = get_object_or_404(OEMProfile.objects.select_related("user"), slug=slug)

    is_staff = request.user.is_authenticated and (request.user.is_superuser or getattr(request.user, "role", "") == "ENGINEER")
    is_owner = request.user.is_authenticated and request.user == oem_profile.user
    is_approved = oem_profile.is_approved and oem_profile.is_verified

    if not (is_approved or is_staff or is_owner):
        raise Http404("OEM profile not found.")

    from django.db.models import Avg
    reviews = oem_profile.reviews.select_related("reviewer").filter(is_approved=True)
    avg_rating = reviews.aggregate(Avg("rating"))["rating__avg"]
    avg_rating = round(avg_rating, 1) if avg_rating else None

    return render(
        request,
        "users/public_oem_profile.html",
        {
            "profile": oem_profile,
            "reviews": reviews,
            "avg_rating": avg_rating,
            "review_count": reviews.count(),
        },
    )

