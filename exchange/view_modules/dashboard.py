from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render

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

    return redirect("login")


# ==============================================================
# OEM DASHBOARD
# ==============================================================


@login_required
def oem_dashboard(request):

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

    # ----------------------------------------------------------
    # RENDER
    # ----------------------------------------------------------

    return render(
        request,
        "exchange/oem_dashboard.html",
        {
            "jobs": jobs,
        },
    )


# ==============================================================
# VENDOR DASHBOARD
# ==============================================================


@login_required
def vendor_dashboard(request):

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
                # AVAILABLE REQUIREMENTS
                # ------------------------------------------------

                Q(
                    status="PUBLISHED"
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

    return render(
        request,
        "exchange/vendor_dashboard.html",
        {
            "jobs": jobs,
            "my_bids": my_bids,
            "awarded_jobs": awarded_jobs,

            # --------------------------------------------------
            # IMPORTANT
            # --------------------------------------------------
            # This makes notifications available to the
            # vendor_dashboard.html template.
            # --------------------------------------------------


        },
    )


# ==============================================================
# ENGINEER DASHBOARD
# ==============================================================


@login_required
def engineer_dashboard(request):

    # ----------------------------------------------------------
    # ENGINEER SECURITY
    # ----------------------------------------------------------

    if (
        request.user.role != "ENGINEER"
        and not request.user.is_superuser
    ):
        return HttpResponseForbidden(
            "Security Block: Restricted to Primexa staff engineers."
        )

    # ----------------------------------------------------------
    # ALL MANUFACTURING REQUIREMENTS
    # ----------------------------------------------------------

    jobs = (
        CADModel.objects
        .all()
        .order_by("-uploaded_at")
    )

    # ----------------------------------------------------------
    # ACTIVE DELIVERY RISK ALERTS
    # ----------------------------------------------------------
    #
    # Vendor submits:
    #
    #     DeliveryRiskAlert.status = OPEN
    #
    # Engineer sees:
    #
    #     OPEN
    #     UNDER_REVIEW
    #     RECOVERY_REQUESTED
    #
    # RESOLVED and ACCEPTED alerts are intentionally removed
    # from the active-alert section.
    # ----------------------------------------------------------

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

    # ----------------------------------------------------------
    # ENGINEER NOTIFICATIONS
    # ----------------------------------------------------------
    #
    # NotificationLog is used to provide the engineer with
    # recent system notifications.
    #
    # Example:
    #
    # - Requirement submitted
    # - Vendor bid
    # - OEM approval
    # - OEM rejection
    # - FAI submitted
    # - Delivery risk alert
    #
    # ----------------------------------------------------------

    notifications = (
        NotificationLog.objects
        .filter(
            recipient=request.user
        )
        .order_by("-created_at")[:20]
    )

    # ----------------------------------------------------------
    # RENDER ENGINEER DASHBOARD
    # ----------------------------------------------------------

    return render(
        request,
        "exchange/engineer_dashboard.html",
        {
            "jobs": jobs,
            "delivery_risk_alerts": delivery_risk_alerts,
            "notifications": notifications,
        },
    )
# ==============================================================
# NOTIFICATIONS
# ==============================================================


@login_required
def notifications(request):

    # ----------------------------------------------------------
    # SECURITY
    # ----------------------------------------------------------

    if (
        not request.user.is_authenticated
    ):
        return redirect("login")

    # ----------------------------------------------------------
    # GET USER NOTIFICATIONS
    # ----------------------------------------------------------

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

    # ----------------------------------------------------------
    # RENDER
    # ----------------------------------------------------------

    return render(
        request,
        "exchange/notifications.html",
        {
            "notifications": user_notifications,
        },
    )