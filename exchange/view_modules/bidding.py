from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from ..forms import BidForm
from ..models import Bid, CADModel, WorkloadTransfer

from ..services.notifications import (
    notify_bid_submitted,
    notify_commercial_proposal,
)


# ==============================================================
# VENDOR — PLACE / MODIFY BID
# ==============================================================


@login_required
def place_bid_view(request, file_id):
    """
    Vendor bid creation and modification.

    First visit:
        Creates a new bid.

    If vendor already has a bid:
        Loads the existing bid and allows modification.

    Important:
        A vendor can have only one active bid per requirement
        through this interface.

    Vendor cannot modify a bid after the requirement has been
    commercially selected / awarded.
    """

    # ----------------------------------------------------------
    # ACCESS CONTROL
    # ----------------------------------------------------------

    if (
        request.user.role != "VENDOR"
        and not request.user.is_superuser
    ):
        return HttpResponseForbidden(
            "Security Block: Only verified vendors can place bids."
        )

    # ----------------------------------------------------------
    # GET REQUIREMENT
    # ----------------------------------------------------------

    cad_file = get_object_or_404(
        CADModel,
        id=file_id,
    )

    # ----------------------------------------------------------
    # PREVENT BID MODIFICATION AFTER AWARD / COMMERCIAL LOCK
    # ----------------------------------------------------------

    locked_statuses = [
        "OEM_APPROVAL_PENDING",
        "OEM_APPROVED",
        "VENDOR_AWARDED",
        "FINAL_VENDOR_ONBOARDED",
        "FAI_PENDING",
        "FAI_APPROVED",
        "COMPLETED",
    ]

    if cad_file.status in locked_statuses:

        return HttpResponseForbidden(
            "This requirement is commercially locked. "
            "Vendor bids can no longer be modified."
        )

    # ----------------------------------------------------------
    # REQUIREMENT MUST BE OPEN FOR BIDDING
    # ----------------------------------------------------------

    if cad_file.status not in [
        "PUBLISHED",
        "BID_PLACED",
    ]:

        return HttpResponseForbidden(
            "This manufacturing requirement is not currently "
            "open for bidding."
        )

    # ----------------------------------------------------------
    # NDA VERIFICATION
    # ----------------------------------------------------------

    has_signed = (
        WorkloadTransfer.objects
        .filter(
            cad_model=cad_file,
            sub_vendor=request.user,
            nda_signed_by_sub=True,
        )
        .exists()
    )

    if (
        not has_signed
        and not request.user.is_superuser
    ):

        return redirect(
            "sign_nda",
            file_id=cad_file.id,
        )

    # ----------------------------------------------------------
    # GET EXISTING BID
    # ----------------------------------------------------------
    #
    # If this vendor has already submitted a bid for this
    # requirement, we load it instead of creating another one.
    #
    # The newest record is used if historical duplicate bids
    # already exist from earlier testing.
    # ----------------------------------------------------------

    existing_bid = (
        Bid.objects
        .filter(
            cad_model=cad_file,
            vendor=request.user,
        )
        .order_by("-id")
        .first()
    )

    # ----------------------------------------------------------
    # POST
    # ----------------------------------------------------------

    if request.method == "POST":

        # ------------------------------------------------------
        # EXISTING BID → UPDATE
        # ------------------------------------------------------

        if existing_bid:

            form = BidForm(
                request.POST,
                instance=existing_bid,
            )

        # ------------------------------------------------------
        # NO BID → CREATE
        # ------------------------------------------------------

        else:

            form = BidForm(
                request.POST,
            )

        # ------------------------------------------------------
        # VALIDATE
        # ------------------------------------------------------

        if form.is_valid():

            bid = form.save(
                commit=False,
            )

            # Always enforce ownership server-side.
            bid.cad_model = cad_file
            bid.vendor = request.user

            bid.save()

            # --------------------------------------------------
            # REQUIREMENT STATUS
            # --------------------------------------------------

            if cad_file.status in [
                "PENDING",
                "PUBLISHED",
            ]:

                cad_file.status = "BID_PLACED"

                cad_file.save(
                    update_fields=[
                        "status",
                    ]
                )

            # --------------------------------------------------
            # NOTIFY ENGINEERING
            # --------------------------------------------------
            #
            # This works for both:
            #
            # NEW BID
            # and
            # MODIFIED BID
            #
            # The notification service receives the latest bid.
            # --------------------------------------------------

            notify_bid_submitted(
                cad_file,
                bid,
            )

            # --------------------------------------------------
            # RETURN TO VENDOR DASHBOARD
            # --------------------------------------------------

            return redirect(
                "vendor_dashboard",
            )

    # ----------------------------------------------------------
    # GET — LOAD EXISTING BID OR EMPTY FORM
    # ----------------------------------------------------------

    else:

        if existing_bid:

            form = BidForm(
                instance=existing_bid,
            )

        else:

            form = BidForm()

    # ----------------------------------------------------------
    # PAGE
    # ----------------------------------------------------------

    return render(
        request,
        "exchange/place_bid.html",
        {
            "form": form,
            "cad_file": cad_file,
            "existing_bid": existing_bid,
            "is_editing": existing_bid is not None,
        },
    )


# ==============================================================
# PRIMEXA INTERNAL BID MANAGEMENT
# ==============================================================


@login_required
def primexa_manage_bids(
    request,
    file_id,
):

    # ----------------------------------------------------------
    # ACCESS CONTROL
    # ----------------------------------------------------------

    if (
        request.user.role != "ENGINEER"
        and not request.user.is_superuser
    ):
        return HttpResponseForbidden(
            "Security Block: Restricted to Primexa staff engineers."
        )

    # ----------------------------------------------------------
    # GET REQUIREMENT
    # ----------------------------------------------------------

    cad_file = get_object_or_404(
        CADModel,
        id=file_id,
    )

    # ----------------------------------------------------------
    # GET BIDS
    # ----------------------------------------------------------

    bids = (
        cad_file.bids
        .all()
        .order_by("offered_price")
    )

    # ----------------------------------------------------------
    # POST — SELECT BID
    # ----------------------------------------------------------

    if request.method == "POST":

        winning_bid_id = request.POST.get(
            "winning_bid_id"
        )

        if not winning_bid_id:

            return HttpResponseForbidden(
                "Please select a vendor bid."
            )

        # ------------------------------------------------------
        # PRIMEXA MARGIN
        # ------------------------------------------------------

        try:

            margin_pct = Decimal(
                str(
                    request.POST.get(
                        "margin_percentage",
                        "15.00",
                    )
                )
            )

        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ):

            return HttpResponseForbidden(
                "Invalid Primexa margin percentage."
            )

        if margin_pct < Decimal("0"):

            return HttpResponseForbidden(
                "Margin percentage cannot be negative."
            )

        if margin_pct > Decimal("100"):

            return HttpResponseForbidden(
                "Margin percentage cannot exceed 100%."
            )

        # ------------------------------------------------------
        # SELECTED BID
        # ------------------------------------------------------

        winning_bid = get_object_or_404(
            Bid,
            id=winning_bid_id,
            cad_model=cad_file,
        )

        vendor_cost = (
            winning_bid.offered_price
        )

        # ------------------------------------------------------
        # COMMERCIAL CALCULATION
        # ------------------------------------------------------

        primexa_quote = (
            vendor_cost
            * (
                Decimal("1")
                + (
                    margin_pct
                    / Decimal("100")
                )
            )
        ).quantize(
            Decimal("0.01")
        )

        # ------------------------------------------------------
        # STORE COMMERCIAL PROPOSAL
        #
        # IMPORTANT:
        #
        # Selecting a vendor does NOT award the vendor.
        #
        # OEM approval remains mandatory.
        # ------------------------------------------------------

        cad_file.selected_vendor = (
            winning_bid.vendor
        )

        cad_file.accepted_vendor_cost = (
            vendor_cost
        )

        cad_file.platform_margin_percentage = (
            margin_pct
        )

        cad_file.final_primexa_quote = (
            primexa_quote
        )

        cad_file.status = (
            "OEM_APPROVAL_PENDING"
        )

        cad_file.save()

        # ------------------------------------------------------
        # NOTIFY OEM
        # ------------------------------------------------------

        notify_commercial_proposal(
            cad_model=cad_file,
            winning_bid=winning_bid,
            margin_percentage=margin_pct,
            vendor_cost=vendor_cost,
            primexa_quote=primexa_quote,
        )

        # ------------------------------------------------------
        # ENGINEER DASHBOARD
        # ------------------------------------------------------

        return redirect(
            "engineer_dashboard"
        )

    # ----------------------------------------------------------
    # DISPLAY BID MANAGEMENT
    # ----------------------------------------------------------

    return render(
        request,
        "exchange/primexa_manage_bids.html",
        {
            "cad_file": cad_file,
            "bids": bids,
        },
    )