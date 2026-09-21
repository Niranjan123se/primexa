from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from users.models import ExpertProfile, OEMProfile, Review, VendorProfile


@login_required
def submit_review(request):
    """Submit a Google-style rating & review for a Vendor, OEM, or Expert profile."""
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid request method.")

    rating_val = request.POST.get("rating", "5")
    try:
        rating = int(rating_val)
        if not (1 <= rating <= 5):
            rating = 5
    except ValueError:
        rating = 5

    title = request.POST.get("title", "").strip()
    comment = request.POST.get("comment", "").strip()

    redirect_url = request.META.get("HTTP_REFERER", "dashboard")

    if not comment:
        messages.error(request, "Review comment cannot be empty.")
        return redirect(redirect_url)

    vendor_slug = request.POST.get("vendor_slug")
    oem_slug = request.POST.get("oem_slug")
    expert_slug = request.POST.get("expert_slug")

    if vendor_slug:
        vendor_profile = get_object_or_404(VendorProfile.objects.select_related("user"), public_slug=vendor_slug)
        if vendor_profile.user == request.user:
            messages.error(request, "Security Block: You cannot write a review for your own business profile.")
            return redirect(redirect_url)
        Review.objects.create(
            reviewer=request.user,
            vendor_profile=vendor_profile,
            rating=rating,
            title=title,
            comment=comment,
        )
        messages.success(request, f"Thank you! Your review for '{vendor_profile.user.company_name}' has been published.")

    elif oem_slug:
        oem_profile = get_object_or_404(OEMProfile.objects.select_related("user"), slug=oem_slug)
        if oem_profile.user == request.user:
            messages.error(request, "Security Block: You cannot write a review for your own business profile.")
            return redirect(redirect_url)
        Review.objects.create(
            reviewer=request.user,
            oem_profile=oem_profile,
            rating=rating,
            title=title,
            comment=comment,
        )
        messages.success(request, f"Thank you! Your review for '{oem_profile.user.company_name}' has been published.")

    elif expert_slug:
        expert_profile = get_object_or_404(ExpertProfile.objects.select_related("user"), slug=expert_slug)
        if expert_profile.user == request.user:
            messages.error(request, "Security Block: You cannot write a review for your own profile.")
            return redirect(redirect_url)
        Review.objects.create(
            reviewer=request.user,
            expert_profile=expert_profile,
            rating=rating,
            title=title,
            comment=comment,
        )
        name = expert_profile.user.get_full_name() or expert_profile.user.username
        messages.success(request, f"Thank you! Your review for expert '{name}' has been published.")

    return redirect(redirect_url)

