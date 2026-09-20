from django.shortcuts import get_object_or_404, render, redirect
from django.db.models import Q
from django.urls import reverse
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required

from .forms import (
    OEMRegistrationForm,
    VendorRegistrationForm,
    UserProfileForm,
    VendorProfileForm,
    OEMProfileForm,
    ExpertProfileForm,
    ExpertRegistrationForm,
    ServiceRequestForm,
)
from .models import ExpertProfile


# ==========================================================
# TERMS & CONDITIONS
# ==========================================================

def terms_conditions(request):
    return render(
        request,
        "users/terms_conditions.html",
    )


# ==========================================================
# OEM REGISTRATION
# ==========================================================

def register_oem(request):

    if request.method == "POST":

        form = OEMRegistrationForm(
            request.POST
        )

        profile_form = OEMProfileForm(
            request.POST
        )

        if (
            form.is_valid()
            and profile_form.is_valid()
        ):

            user = form.save(
                commit=False
            )

            user.role = "OEM"
            user.save()

            profile = profile_form.save(
                commit=False
            )

            profile.user = user
            profile.save()

            login(
                request,
                user,
            )

            return redirect(
                "oem_dashboard"
            )

    else:

        form = OEMRegistrationForm()
        profile_form = OEMProfileForm()

    return render(
        request,
        "users/register_oem.html",
        {
            "form": form,
            "profile_form": profile_form,
        },
    )


# ==========================================================
# VENDOR REGISTRATION
# ==========================================================

def register_vendor(request):

    if request.method == "POST":

        form = VendorRegistrationForm(
            request.POST
        )

        profile_form = VendorProfileForm(
            request.POST,
            request.FILES,
        )

        if (
            form.is_valid()
            and profile_form.is_valid()
        ):

            user = form.save(
                commit=False
            )

            user.role = "VENDOR"
            user.save()

            profile = profile_form.save(
                commit=False
            )

            profile.user = user
            profile.save()

            login(
                request,
                user,
            )

            return redirect(
                "vendor_dashboard"
            )

    else:

        form = VendorRegistrationForm()
        profile_form = VendorProfileForm()

    return render(
        request,
        "users/register_vendor.html",
        {
            "form": form,
            "profile_form": profile_form,
        },
    )


# ==========================================================
# EXPERT REGISTRATION AND SERVICE REQUESTS
# ==========================================================

def register_expert(request):
    """Register an independent expert without granting staff access."""
    if request.method == "POST":
        form = ExpertRegistrationForm(request.POST)
        profile_form = ExpertProfileForm(request.POST)
        if form.is_valid() and profile_form.is_valid():
            user = form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            login(request, user)
            return redirect("expert_dashboard")
    else:
        form = ExpertRegistrationForm()
        profile_form = ExpertProfileForm()

    return render(
        request,
        "users/register_expert.html",
        {"form": form, "profile_form": profile_form},
    )


def request_service(request):
    """Capture an enquiry for vendor, expert, or end-to-end assistance."""
    if request.method == "POST":
        form = ServiceRequestForm(request.POST)
        if form.is_valid():
            service_request = form.save(commit=False)
            if request.user.is_authenticated:
                service_request.submitted_by = request.user
            service_request.save()
            return render(request, "users/service_request_success.html")
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {
                "contact_name": request.user.get_full_name() or request.user.username,
                "contact_email": request.user.email,
                "contact_phone": request.user.phone_number,
                "company_name": request.user.company_name,
            }
        expert_name = request.GET.get("expert", "").strip()
        if expert_name:
            initial["request_type"] = "FIND_EXPERT"
            initial["project_title"] = f"Booking request for {expert_name}"
        form = ServiceRequestForm(initial=initial)

    return render(request, "users/service_request.html", {"form": form})


def expert_directory(request):
    filters = {
        "q": request.GET.get("q", "").strip(),
        "city": request.GET.get("city", "").strip(),
        "available": request.GET.get("available", "") == "1",
    }
    experts = ExpertProfile.objects.filter(is_public_profile=True).select_related("user")
    if filters["q"]:
        experts = experts.filter(
            Q(headline__icontains=filters["q"])
            | Q(expertise__icontains=filters["q"])
            | Q(industries__icontains=filters["q"])
        )
    if filters["city"]:
        experts = experts.filter(city__iexact=filters["city"])
    if filters["available"]:
        experts = experts.filter(is_available=True)
    cities = ExpertProfile.objects.filter(is_public_profile=True).exclude(city="").values_list("city", flat=True).distinct().order_by("city")
    return render(request, "users/expert_directory.html", {"experts": experts, "filters": filters, "cities": cities})


def public_expert_profile(request, expert_id):
    profile = get_object_or_404(
        ExpertProfile.objects.select_related("user"),
        pk=expert_id,
        is_public_profile=True,
    )
    return render(request, "users/public_expert_profile.html", {"profile": profile})


# ==========================================================
# CENTRAL DASHBOARD ROUTER
# ==========================================================

@login_required
def dashboard(request):

    user = request.user

    if (
        user.is_superuser
        or user.role == "ENGINEER"
    ):
        return redirect(
            "engineer_dashboard"
        )

    if user.role == "OEM":
        return redirect(
            "oem_dashboard"
        )

    if user.role == "VENDOR":
        return redirect(
            "vendor_dashboard"
        )

    if user.role == "EXPERT":
        return redirect("expert_dashboard")

    logout(request)

    return redirect(
        "login"
    )


# ==========================================================
# PROFILE
# ==========================================================

@login_required
def profile(request):
    """
    Central profile page.

    OEM:
        UserProfileForm + OEMProfileForm

    Vendor:
        UserProfileForm + VendorProfileForm

    Engineer:
        Basic UserProfileForm only.
    """

    user = request.user

    # ======================================================
    # VENDOR
    # ======================================================

    if user.role == "VENDOR":

        try:
            vendor_profile = user.vendor_profile

        except Exception:

            from .models import VendorProfile

            vendor_profile = VendorProfile.objects.create(
                user=user
            )

        if request.method == "POST":

            user_form = UserProfileForm(
                request.POST,
                instance=user,
            )

            profile_form = VendorProfileForm(
                request.POST,
                request.FILES,
                instance=vendor_profile,
            )

            if (
                user_form.is_valid()
                and profile_form.is_valid()
            ):

                user_form.save()

                profile_form.save()

                return redirect(
                    "profile"
                )

        else:

            user_form = UserProfileForm(
                instance=user,
            )

            profile_form = VendorProfileForm(
                instance=vendor_profile,
            )

        return render(
            request,
            "users/vendor_profile.html",
            {
                "user_form": user_form,
                "profile_form": profile_form,
                "profile_type": "VENDOR",
                "profile_object": vendor_profile,
            },
        )

    # ======================================================
    # OEM
    # ======================================================

    if user.role == "OEM":

        try:
            oem_profile = user.oem_profile

        except Exception:

            from .models import OEMProfile

            oem_profile = OEMProfile.objects.create(
                user=user
            )

        if request.method == "POST":

            user_form = UserProfileForm(
                request.POST,
                instance=user,
            )

            profile_form = OEMProfileForm(
                request.POST,
                instance=oem_profile,
            )

            if (
                user_form.is_valid()
                and profile_form.is_valid()
            ):

                user_form.save()

                profile_form.save()

                return redirect(
                    "profile"
                )

        else:

            user_form = UserProfileForm(
                instance=user,
            )

            profile_form = OEMProfileForm(
                instance=oem_profile,
            )

        return render(
            request,
            "users/oem_profile.html",
            {
                "user_form": user_form,
                "profile_form": profile_form,
                "profile_type": "OEM",
                "profile_object": oem_profile,
            },
        )

    # ======================================================
    # EXPERT
    # ======================================================

    if user.role == "EXPERT":
        expert_profile, _ = ExpertProfile.objects.get_or_create(user=user)

        if request.method == "POST":
            user_form = UserProfileForm(request.POST, instance=user)
            profile_form = ExpertProfileForm(request.POST, instance=expert_profile)
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                return redirect("profile")
        else:
            user_form = UserProfileForm(instance=user)
            profile_form = ExpertProfileForm(instance=expert_profile)

        return render(
            request,
            "users/expert_profile.html",
            {
                "user_form": user_form,
                "profile_form": profile_form,
                "profile_type": "EXPERT",
                "profile_object": expert_profile,
            },
        )

    # ======================================================
    # ENGINEER / SUPERUSER
    # ======================================================

    if request.method == "POST":

        user_form = UserProfileForm(
            request.POST,
            instance=user,
        )

        if user_form.is_valid():

            user_form.save()

            return redirect(
                "profile"
            )

    else:

        user_form = UserProfileForm(
            instance=user,
        )

    return render(
        request,
        "users/profile.html",
        {
            "user_form": user_form,
            "profile_type": "ENGINEER",
        },
    )


# ==========================================================
# LOGOUT
# ==========================================================

def logout_user(request):

    logout(request)

    return redirect(
        "login"
    )


@login_required
def expert_dashboard(request):
    if request.user.role != "EXPERT":
        return redirect("dashboard")

    profile, _ = ExpertProfile.objects.get_or_create(user=request.user)
    return render(
        request,
        "users/expert_dashboard.html",
        {
            "profile": profile,
            "service_requests": request.user.service_requests.all()[:10],
            "public_profile_url": reverse(
                "public_expert_profile", kwargs={"expert_id": profile.id}
            ),
        },
    )
