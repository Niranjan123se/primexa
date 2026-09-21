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
            profile.is_public_profile = True
            profile.is_public_profile_approved = True
            profile.is_verified = True
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

            from exchange.services.notifications import send_notification
            from .models import User

            engineers = User.objects.filter(role="ENGINEER", is_active=True)
            for engineer in engineers:
                send_notification(
                    notification_type="SERVICE_REQUEST_SUBMITTED",
                    recipient=engineer,
                    subject=f"[Primexa Help Request] {service_request.project_title}",
                    message=(
                        f"A new help & assistance request has been submitted.\n\n"
                        f"Project Title: {service_request.project_title}\n"
                        f"Request Type: {service_request.get_request_type_display()}\n"
                        f"Contact Name: {service_request.contact_name}\n"
                        f"Email: {service_request.contact_email}\n"
                        f"Phone: {service_request.contact_phone}\n"
                        f"Company: {service_request.company_name}\n\n"
                        f"Description:\n{service_request.task_description}\n\n"
                        f"Review and process this request in the Engineering Dashboard."
                    ),
                )

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


def public_expert_profile(request, slug=None, expert_id=None):
    from django.http import Http404
    from django.db.models import Avg
    if slug:
        profile = get_object_or_404(ExpertProfile.objects.select_related("user"), slug=slug)
    else:
        profile = get_object_or_404(ExpertProfile.objects.select_related("user"), pk=expert_id)

    is_staff = request.user.is_authenticated and (request.user.is_superuser or getattr(request.user, "role", "") == "ENGINEER")
    is_owner = request.user.is_authenticated and request.user == profile.user
    is_approved = profile.is_public_profile and profile.is_verified

    if not (is_approved or is_staff or is_owner):
        raise Http404("Expert profile not found.")

    reviews = profile.reviews.select_related("reviewer").filter(is_approved=True)
    avg_rating = reviews.aggregate(Avg("rating"))["rating__avg"]
    avg_rating = round(avg_rating, 1) if avg_rating else None

    return render(
        request,
        "users/public_expert_profile.html",
        {
            "profile": profile,
            "photos": profile.photos.all(),
            "certificates": profile.certificates.all(),
            "reviews": reviews,
            "avg_rating": avg_rating,
            "review_count": reviews.count(),
        },
    )



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
    assigned_reqs = profile.assigned_requests.all().order_by("-created_at")
    return render(
        request,
        "users/expert_dashboard.html",
        {
            "profile": profile,
            "service_requests": assigned_reqs[:10],
            "public_profile_url": reverse(
                "public_expert_profile", kwargs={"slug": profile.slug}
            ) if profile.slug else None,
        },
    )


from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from .models import ExpertPhoto, ExpertCertificate, ServiceRequest

@login_required
def add_expert_photo(request):
    if request.user.role != "EXPERT":
        return HttpResponseForbidden("Access restricted to experts.")
    profile = get_object_or_404(ExpertProfile, user=request.user)
    if request.method == "POST" and request.FILES.get("image"):
        caption = request.POST.get("caption", "").strip()
        ExpertPhoto.objects.create(expert_profile=profile, image=request.FILES["image"], caption=caption)
        messages.success(request, "Portfolio photo uploaded successfully.")
    return redirect("profile")


@login_required
def delete_expert_photo(request, photo_id):
    if request.user.role != "EXPERT":
        return HttpResponseForbidden("Access restricted to experts.")
    photo = get_object_or_404(ExpertPhoto, id=photo_id, expert_profile__user=request.user)
    photo.delete()
    messages.success(request, "Portfolio photo deleted.")
    return redirect("profile")


@login_required
def add_expert_certificate(request):
    if request.user.role != "EXPERT":
        return HttpResponseForbidden("Access restricted to experts.")
    profile = get_object_or_404(ExpertProfile, user=request.user)
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        issuing_org = request.POST.get("issuing_organization", "").strip()
        issue_date = request.POST.get("issue_date") or None
        cert_file = request.FILES.get("certificate_file")
        if title:
            ExpertCertificate.objects.create(
                expert_profile=profile,
                title=title,
                issuing_organization=issuing_org,
                issue_date=issue_date,
                certificate_file=cert_file,
            )
            messages.success(request, "Certificate uploaded successfully.")
    return redirect("profile")


@login_required
def delete_expert_certificate(request, cert_id):
    if request.user.role != "EXPERT":
        return HttpResponseForbidden("Access restricted to experts.")
    cert = get_object_or_404(ExpertCertificate, id=cert_id, expert_profile__user=request.user)
    cert.delete()
    messages.success(request, "Certificate deleted.")
    return redirect("profile")


@login_required
def expert_respond_service_request(request, request_id):
    """Allows an expert to accept/decline or mark unavailable with feedback notes."""
    if request.user.role != "EXPERT":
        return HttpResponseForbidden("Access restricted to independent manufacturing experts.")

    expert_profile = get_object_or_404(ExpertProfile, user=request.user)
    service_req = get_object_or_404(ServiceRequest, id=request_id, assigned_expert=expert_profile)

    if request.method == "POST":
        response_choice = request.POST.get("expert_response", "ACCEPTED")
        feedback_notes = request.POST.get("expert_feedback_notes", "").strip()

        service_req.expert_response = response_choice
        service_req.expert_feedback_notes = feedback_notes
        service_req.expert_responded_at = timezone.now()
        service_req.save()

        messages.success(request, f"Your feedback response ('{response_choice}') has been recorded.")
        return redirect("expert_dashboard")

    return render(request, "users/expert_respond_request.html", {"service_req": service_req})


@login_required
def engineer_bulk_invite_experts(request):
    """Primexa staff engineers can filter experts and send bulk job invitations."""
    if not (request.user.is_superuser or request.user.role == "ENGINEER"):
        return HttpResponseForbidden("Security Block: Primexa staff engineer access required.")

    if request.method == "POST":
        expert_ids = request.POST.getlist("expert_ids")
        project_title = request.POST.get("project_title", "").strip()
        task_description = request.POST.get("task_description", "").strip()

        if expert_ids and project_title and task_description:
            experts = ExpertProfile.objects.filter(id__in=expert_ids)
            for exp in experts:
                ServiceRequest.objects.create(
                    submitted_by=request.user,
                    assigned_expert=exp,
                    request_type="FIND_EXPERT",
                    project_title=project_title,
                    task_description=task_description,
                    contact_name=request.user.get_full_name() or request.user.username,
                    contact_email=request.user.email,
                    contact_phone=request.user.phone_number,
                    company_name="Primexa Engineering Control",
                )
            messages.success(request, f"Bulk job invitations sent to {experts.count()} experts!")
        else:
            messages.error(request, "Please select experts and enter project title and description.")

    return redirect("expert_directory")


@login_required
def toggle_user_active_status(request, user_id):
    """Staff Engineers can suspend or activate any user account."""
    if not (request.user.is_superuser or request.user.role == "ENGINEER"):
        return HttpResponseForbidden("Security Block: Primexa staff engineer access required.")

    from .models import User
    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        messages.error(request, "You cannot suspend your own admin account.")
        return redirect("engineer_dashboard")

    target_user.is_active = not target_user.is_active
    target_user.save(update_fields=["is_active"])

    status_str = "activated" if target_user.is_active else "suspended"
    messages.success(request, f"User account '{target_user.username}' ({target_user.get_full_name() or target_user.company_name}) has been {status_str}.")
    return redirect("engineer_dashboard")


@login_required
def delete_user_account(request, user_id):
    """Staff Engineers can delete a user account."""
    if not (request.user.is_superuser or request.user.role == "ENGINEER"):
        return HttpResponseForbidden("Security Block: Primexa staff engineer access required.")

    from .models import User
    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        messages.error(request, "You cannot delete your own admin account.")
        return redirect("engineer_dashboard")

    username = target_user.username
    target_user.delete()
    messages.success(request, f"User account '{username}' has been permanently deleted.")
    return redirect("engineer_dashboard")

