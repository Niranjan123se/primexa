from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse

from users.models import VendorProfile, OEMProfile, ExpertProfile

from ..models import (
    CADModel,
    DeliveryRiskAlert,
    NotificationLog,

)



# ==============================================================
# CENTRAL DASHBOARD ROUTER
# ==============================================================


@login_required
def dashboard(request):

    if (
        request.user.is_superuser
        or request.user.role == "ENGINEER"
    ):
        return redirect("engineer_dashboard")

    if request.user.role == "OEM":
        return redirect("oem_dashboard")

    if request.user.role == "VENDOR":
        return redirect("vendor_dashboard")

    if request.user.role == "EXPERT":
        return redirect("expert_dashboard")

    return redirect("login")



# ==============================================================
# OEM DASHBOARD
# ==============================================================


@login_required
def oem_dashboard(request, company_slug=None):

    if (
        request.user.role != "OEM"
        and not request.user.is_superuser
    ):
        return HttpResponseForbidden(
            "Security Block: OEM access required."
        )

    # ----------------------------------------------------------
    # OEM JOBS
    # ----------------------------------------------------------

    jobs = (
        CADModel.objects
        .filter(
            uploaded_by=request.user
        )
        .order_by("-uploaded_at")
    )

    oem_profile, _ = OEMProfile.objects.get_or_create(user=request.user)

    # ----------------------------------------------------------
    # RENDER
    # ----------------------------------------------------------

    return render(
        request,
        "exchange/oem_dashboard.html",
        {
            "jobs": jobs,
            "oem_profile": oem_profile,
            "company_slug": company_slug or oem_profile.slug,
        },
    )


# ==============================================================
# VENDOR DASHBOARD
# ==============================================================


@login_required
def vendor_dashboard(request, company_slug=None):

    if (
        request.user.role != "VENDOR"
        and not request.user.is_superuser
    ):
        return HttpResponseForbidden(
            "Security Block: Vendor access required."
        )

    # ----------------------------------------------------------
    # VENDOR ACCESS LOGIC
    # ----------------------------------------------------------
    #
    # Vendor can see:
    #
    # 1. Published requirements
    # 2. Requirements where THIS vendor has placed a bid
    # 3. Requirements awarded to THIS vendor
    #
    # Vendor must NOT see another vendor's awarded requirements.
    # ----------------------------------------------------------

    if request.user.is_superuser:

        jobs = (
            CADModel.objects
            .all()
            .order_by("-uploaded_at")
        )

    else:

        jobs = (
            CADModel.objects
            .filter(

                # ------------------------------------------------
                # AVAILABLE REQUIREMENTS (OPEN OR TARGETED TO THIS VENDOR)
                # ------------------------------------------------

                (
                    Q(status="PUBLISHED", targeted_vendors__isnull=True)
                    | Q(status="PUBLISHED", targeted_vendors=request.user)
                )

                # ------------------------------------------------
                # REQUIREMENTS WHERE THIS VENDOR BID
                # ------------------------------------------------

                | Q(
                    bids__vendor=request.user
                )

                # ------------------------------------------------
                # REQUIREMENTS AWARDED TO THIS VENDOR
                # ------------------------------------------------

                | Q(
                    selected_vendor=request.user
                )
            )
            .distinct()
            .order_by("-uploaded_at")
        )

    # ----------------------------------------------------------
    # VENDOR NOTIFICATIONS
    # ----------------------------------------------------------
    #
    # This includes:
    #
    # FAI_REQUIRED
    # FAI_SUBMITTED
    # FAI_APPROVED
    # FAI_REJECTED
    # SYSTEM_ALERT
    # etc.
    #
    # Only notifications belonging to the logged-in vendor
    # are returned.
    # ----------------------------------------------------------
    # ----------------------------------------------------------
    # SEPARATE VENDOR INFORMATION
    # ----------------------------------------------------------

    if request.user.is_superuser:

        # ------------------------------------------------------
        # SUPERUSER
        # ------------------------------------------------------

        my_bids = []

        awarded_jobs = (
            CADModel.objects
            .filter(
                status__in=[
                    "VENDOR_AWARDED",
                    "FINAL_VENDOR_ONBOARDED",
                    "FAI_PENDING",
                    "FAI_APPROVED",
                    "COMPLETED",
                ]
            )
            .order_by("-uploaded_at")
        )

    else:

        # ------------------------------------------------------
        # MY BIDS
        # ------------------------------------------------------

        my_bids = (
            CADModel.objects
            .filter(
                bids__vendor=request.user
            )
            .distinct()
            .order_by("-uploaded_at")
        )

        # ------------------------------------------------------
        # MY AWARDED ORDERS
        # ------------------------------------------------------

        awarded_jobs = (
            CADModel.objects
            .filter(
                selected_vendor=request.user,
                status__in=[
                    "VENDOR_AWARDED",
                    "FINAL_VENDOR_ONBOARDED",
                    "FAI_PENDING",
                    "FAI_APPROVED",
                    "COMPLETED",
                ]
            )
            .order_by("-uploaded_at")
        )

    # ----------------------------------------------------------
    # RENDER VENDOR DASHBOARD
    # ----------------------------------------------------------

    public_profile_url = None
    vendor_profile = None
    if not request.user.is_superuser:
        vendor_profile, _ = VendorProfile.objects.get_or_create(user=request.user)
        if vendor_profile.public_slug:
            public_profile_url = reverse(
                "public_vendor_profile", kwargs={"slug": vendor_profile.public_slug}
            )

    return render(
        request,
        "exchange/vendor_dashboard.html",
        {
            "jobs": jobs,
            "my_bids": my_bids,
            "awarded_jobs": awarded_jobs,
            "public_profile_url": public_profile_url,
            "vendor_profile": vendor_profile,
            "company_slug": company_slug or (vendor_profile.public_slug if vendor_profile else None),
        },
    )


# ==============================================================
# ENGINEER DASHBOARD
# ==============================================================


@login_required
def engineer_dashboard(request):

    if (
        request.user.role != "ENGINEER"
        and not request.user.is_superuser
    ):
        return HttpResponseForbidden(
            "Security Block: Restricted to Primexa staff engineers."
        )

    jobs = (
        CADModel.objects
        .all()
        .order_by("-uploaded_at")
    )

    delivery_risk_alerts = (
        DeliveryRiskAlert.objects
        .filter(
            status__in=[
                "OPEN",
                "UNDER_REVIEW",
                "RECOVERY_REQUESTED",
            ]
        )
        .select_related(
            "cad_model",
            "vendor",
            "reviewed_by",
        )
        .order_by("-reported_at")
    )

    notifications = (
        NotificationLog.objects
        .filter(
            recipient=request.user
        )
        .order_by("-created_at")[:20]
    )

    from users.models import VendorProfile, OEMProfile, ExpertProfile, ServiceRequest

    vendors = VendorProfile.objects.select_related("user").all().order_by("-id")
    oems = OEMProfile.objects.select_related("user").all().order_by("-id")
    experts = ExpertProfile.objects.select_related("user").all().order_by("-id")
    service_requests = ServiceRequest.objects.select_related("submitted_by", "assigned_expert__user").all().order_by("-created_at")

    pending_vendors = [v for v in vendors if not (v.is_verified and v.is_public_profile_approved)]
    approved_vendors = [v for v in vendors if (v.is_verified and v.is_public_profile_approved)]

    pending_oems = [o for o in oems if not (o.is_verified and o.is_approved)]
    approved_oems = [o for o in oems if (o.is_verified and o.is_approved)]

    pending_experts = [e for e in experts if not (e.is_verified and e.is_public_profile)]
    approved_experts = [e for e in experts if (e.is_verified and e.is_public_profile)]

    return render(
        request,
        "exchange/engineer_dashboard.html",
        {
            "jobs": jobs,
            "service_requests": service_requests,
            "delivery_risk_alerts": delivery_risk_alerts,
            "notifications": notifications,
            "vendors": vendors,
            "pending_vendors": pending_vendors,
            "approved_vendors": approved_vendors,
            "oems": oems,
            "pending_oems": pending_oems,
            "approved_oems": approved_oems,
            "experts": experts,
            "pending_experts": pending_experts,
            "approved_experts": approved_experts,
        },
    )


# ==============================================================
# NOTIFICATIONS
# ==============================================================


@login_required
def notifications(request):

    if not request.user.is_authenticated:
        return redirect("login")

    user_notifications = (
        NotificationLog.objects
        .filter(
            recipient=request.user
        )
        .select_related(
            "cad_model",
        )
        .order_by(
            "-created_at"
        )
    )

    return render(
        request,
        "exchange/notifications.html",
        {
            "notifications": user_notifications,
        },
    )
