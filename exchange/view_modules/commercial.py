from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import (
    HttpResponseBadRequest,
    HttpResponseForbidden,
)
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone

from ..models import CADModel, Bid


# ==============================================================
# OEM COMMERCIAL APPROVAL
# ==============================================================


@login_required
def oem_approve_quote(request, file_id):
    """
    OEM Commercial Quote Approval.

    GET:
        Displays the final Primexa commercial quotation.

    POST:
        action=approve
        action=reject

    Workflow:

        OEM_APPROVAL_PENDING
                    |
              OEM Decision
             /            \
       APPROVE            REJECT
          |                  |
    OEM_APPROVED       OEM_REJECTED
    """

    # ----------------------------------------------------------
    # GET REQUIREMENT
    # ----------------------------------------------------------

    cad_file = get_object_or_404(
        CADModel,
        id=file_id,
    )

    # ----------------------------------------------------------
    # ACCESS CONTROL
    # ----------------------------------------------------------

    if (
        request.user.role != "OEM"
        and not request.user.is_superuser
    ):
        return HttpResponseForbidden(
            "Security Block: Only the OEM can approve this commercial quote."
        )

    # ----------------------------------------------------------
    # VERIFY OEM OWNERSHIP
    # ----------------------------------------------------------

    if (
        cad_file.uploaded_by != request.user
        and not request.user.is_superuser
    ):
        return HttpResponseForbidden(
            "Security Block: You are not authorized to approve this requirement."
        )

    # ----------------------------------------------------------
    # VERIFY CURRENT STATUS
    # ----------------------------------------------------------

    if cad_file.status != "OEM_APPROVAL_PENDING":
        return HttpResponseForbidden(
            "Commercial approval is not available for the current "
            f"requirement status: {cad_file.get_status_display()}"
        )

    # ----------------------------------------------------------
    # POST
    # ----------------------------------------------------------

    if request.method == "POST":

        action = (
            request.POST
            .get("action", "")
            .strip()
            .lower()
        )

        remarks = (
            request.POST
            .get("remarks", "")
            .strip()
        )

        # ======================================================
        # APPROVE QUOTE
        # ======================================================

        if action == "approve":

            cad_file.status = "OEM_APPROVED"

            if hasattr(
                cad_file,
                "oem_approval_remarks",
            ):
                cad_file.oem_approval_remarks = remarks

            if hasattr(
                cad_file,
                "oem_approval_at",
            ):
                cad_file.oem_approval_at = timezone.now()

            if hasattr(
                cad_file,
                "oem_approved_by",
            ):
                cad_file.oem_approved_by = request.user

            cad_file.save()

            return redirect(
                "oem_dashboard"
            )

        # ======================================================
        # REJECT QUOTE
        # ======================================================

        if action == "reject":

            cad_file.status = "OEM_REJECTED"

            if hasattr(
                cad_file,
                "oem_approval_remarks",
            ):
                cad_file.oem_approval_remarks = remarks

            if hasattr(
                cad_file,
                "oem_approval_at",
            ):
                cad_file.oem_approval_at = timezone.now()

            if hasattr(
                cad_file,
                "oem_approved_by",
            ):
                cad_file.oem_approved_by = request.user

            cad_file.save()

            return redirect(
                "oem_dashboard"
            )

        # ======================================================
        # INVALID ACTION
        # ======================================================

        return HttpResponseBadRequest(
            "Invalid approval decision."
        )

    # ==========================================================
    # DISPLAY APPROVAL PAGE
    # ==========================================================

    return render(
        request,
        "exchange/oem_approve_quote.html",
        {
            "cad_file": cad_file,
        },
    )


# ==============================================================
# FINAL VENDOR AWARD
# ==============================================================


@login_required
def final_vendor_award(request, file_id):
    """
    Final Vendor Award.

    This action is performed internally by Primexa after the OEM
    approves the final commercial quotation.

    Workflow:

        OEM_APPROVED
              |
        Primexa Engineer
              |
        Final Vendor Award
              |
        VENDOR_AWARDED

    At the time of award, the vendor's committed delivery date
    is automatically calculated from the vendor's accepted bid.
    """

    # ----------------------------------------------------------
    # GET REQUIREMENT
    # ----------------------------------------------------------

    cad_file = get_object_or_404(
        CADModel,
        id=file_id,
    )

    # ----------------------------------------------------------
    # ACCESS CONTROL
    # ----------------------------------------------------------

    if (
        request.user.role != "ENGINEER"
        and not request.user.is_superuser
    ):
        return HttpResponseForbidden(
            "Security Block: Only Primexa engineers can issue the final vendor award."
        )

    # ----------------------------------------------------------
    # VERIFY STATUS
    # ----------------------------------------------------------

    if cad_file.status != "OEM_APPROVED":
        return HttpResponseForbidden(
            "Final vendor award is only available after OEM commercial approval."
        )

    # ----------------------------------------------------------
    # GET SELECTED VENDOR
    # ----------------------------------------------------------

    selected_vendor = getattr(
        cad_file,
        "selected_vendor",
        None,
    )

    if not selected_vendor:
        return HttpResponseForbidden(
            "No vendor has been selected for this requirement."
        )

    # ----------------------------------------------------------
    # GET SELECTED VENDOR BID
    # ----------------------------------------------------------

    winning_bid = (
        Bid.objects
        .filter(
            cad_model=cad_file,
            vendor=selected_vendor,
        )
        .order_by("-created_at")
        .first()
    )

    if not winning_bid:

        return HttpResponseForbidden(
            "No bid was found for the selected vendor. "
            "The final vendor award cannot be issued."
        )

    # ----------------------------------------------------------
    # VALIDATE DELIVERY DAYS
    # ----------------------------------------------------------

    if winning_bid.delivery_days is None:

        return HttpResponseForbidden(
            "The selected vendor's bid does not contain "
            "a delivery commitment."
        )

    if winning_bid.delivery_days < 0:

        return HttpResponseForbidden(
            "The selected vendor has submitted an invalid "
            "delivery commitment."
        )

    # ----------------------------------------------------------
    # POST — FINAL AWARD
    # ----------------------------------------------------------

    if request.method == "POST":

        confirm = (
            request.POST
            .get("confirm", "yes")
            .strip()
            .lower()
        )

        if confirm not in [
            "yes",
            "approve",
            "award",
            "confirm",
        ]:
            return HttpResponseBadRequest(
                "Final vendor award was not confirmed."
            )

        # ======================================================
        # CALCULATE VENDOR COMMITTED DELIVERY DATE
        # ======================================================

        award_date = timezone.localdate()

        vendor_delivery_date = (
            award_date
            + timedelta(
                days=winning_bid.delivery_days
            )
        )

        # ======================================================
        # FINAL AWARD
        # ======================================================

        cad_file.status = "VENDOR_AWARDED"

        # ------------------------------------------------------
        # New delivery commitment
        # ------------------------------------------------------

        if hasattr(
            cad_file,
            "vendor_committed_delivery_date",
        ):

            cad_file.vendor_committed_delivery_date = (
                vendor_delivery_date
            )

        # ------------------------------------------------------
        # Award timestamp
        # ------------------------------------------------------

        if hasattr(
            cad_file,
            "vendor_awarded_at",
        ):

            cad_file.vendor_awarded_at = (
                timezone.now()
            )

        # ------------------------------------------------------
        # Awarding engineer
        # ------------------------------------------------------

        if hasattr(
            cad_file,
            "vendor_awarded_by",
        ):

            cad_file.vendor_awarded_by = (
                request.user
            )

        # ------------------------------------------------------
        # Final vendor
        # ------------------------------------------------------

        if hasattr(
            cad_file,
            "final_vendor",
        ):

            cad_file.final_vendor = (
                selected_vendor
            )

        # ======================================================
        # SAVE
        # ======================================================

        cad_file.save()

        # ------------------------------------------------------
        # REDIRECT
        # ------------------------------------------------------

        return redirect(
            "engineer_dashboard"
        )

    # ==========================================================
    # DISPLAY FINAL AWARD PAGE
    # ==========================================================

    return render(
        request,
        "exchange/final_vendor_award.html",
        {
            "cad_file": cad_file,
            "selected_vendor": selected_vendor,
            "winning_bid": winning_bid,
        },
    )