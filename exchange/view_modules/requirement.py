from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ..forms import (
    CADUploadForm,
    EngineerReviewForm,
)

from ..forms.engineering_process import (
    EngineeringProcessForm,
)

from ..models import (
    CADModel,
    RequirementProcess,
)

from ..services.notifications import (
    notify_requirement_published,
    notify_requirement_submitted,
)


# ==============================================================
# OEM — UPLOAD MANUFACTURING REQUIREMENT
# ==============================================================


@login_required
def upload_job_view(request):

    if (
        request.user.role != "OEM"
        and request.user.role != "ENGINEER"
        and not request.user.is_superuser
    ):
        return HttpResponseForbidden(
            "Security Block: Access restricted to OEMs and Primexa staff engineers."
        )

    if request.method == "POST":

        form = CADUploadForm(
            request.POST,
            request.FILES,
            user=request.user,
        )

        if form.is_valid():

            job = form.save(
                commit=False
            )

            job.uploaded_by = request.user

            # --------------------------------------------------
            # Sourcing Flow Handling
            # --------------------------------------------------
            if job.sourcing_flow == "DIRECT_RFQ":
                job.status = "PUBLISHED"
                job.save()
                form.save_m2m()
                if job.targeted_vendors.exists():
                    for v in job.targeted_vendors.all():
                        notify_requirement_published(job, recipient=v)
                else:
                    notify_requirement_published(job)
            else:
                job.status = "PENDING"
                if hasattr(job, "process_plan_status"):
                    job.process_plan_status = "DRAFT"
                job.save()
                form.save_m2m()
                notify_requirement_submitted(job)

            return redirect("oem_dashboard")

    else:

        form = CADUploadForm(user=request.user)

    return render(
        request,
        "exchange/upload_job.html",
        {
            "form": form,
        },
    )


# ==============================================================
# ENGINEER — REQUIREMENT REVIEW + PROCESS PLANNING
# ==============================================================


@login_required
def review_workload(
    request,
    file_id,
):

    # ----------------------------------------------------------
    # ENGINEER ACCESS
    # ----------------------------------------------------------

    if (
        request.user.role != "ENGINEER"
        and not request.user.is_superuser
    ):
        return HttpResponseForbidden(
            "Security Block: Only Primexa staff engineers can review requirements."
        )

    # ----------------------------------------------------------
    # REQUIREMENT
    # ----------------------------------------------------------

    cad_file = get_object_or_404(
        CADModel,
        id=file_id,
    )

    # ----------------------------------------------------------
    # EXISTING MANUFACTURING OPERATIONS
    # ----------------------------------------------------------

    processes = (
        RequirementProcess.objects
        .filter(
            cad_model=cad_file,
        )
        .order_by(
            "sequence",
        )
    )

    # ----------------------------------------------------------
    # PROCESS PLAN LOCK
    #
    # Once published, the engineering route is locked.
    # ----------------------------------------------------------

    plan_locked = (
        getattr(
            cad_file,
            "process_plan_status",
            None,
        )
        == "APPROVED"
        and cad_file.status == "PUBLISHED"
    )

    # ----------------------------------------------------------
    # POST
    # ----------------------------------------------------------

    if request.method == "POST":

        action = request.POST.get(
            "action"
        )

        # ======================================================
        # ADD MANUFACTURING PROCESS
        # ======================================================

        if action == "add_process":

            if plan_locked:

                return HttpResponseForbidden(
                    "This requirement has already been published to vendors."
                )

            process_form = EngineeringProcessForm(
                request.POST
            )

            if process_form.is_valid():

                sequence = process_form.cleaned_data[
                    "sequence"
                ]

                # --------------------------------------------------
                # Prevent duplicate sequence numbers
                # --------------------------------------------------

                duplicate = (
                    RequirementProcess.objects
                    .filter(
                        cad_model=cad_file,
                        sequence=sequence,
                    )
                    .exists()
                )

                if duplicate:

                    process_form.add_error(
                        "sequence",
                        (
                            "This sequence number already exists "
                            "for this requirement."
                        ),
                    )

                else:

                    process = process_form.save(
                        commit=False
                    )

                    process.cad_model = cad_file

                    process.save()

                    # --------------------------------------------------
                    # Record engineer who created the plan
                    # --------------------------------------------------

                    if hasattr(
                        cad_file,
                        "process_plan_created_by",
                    ):

                        if not cad_file.process_plan_created_by:

                            cad_file.process_plan_created_by = (
                                request.user
                            )

                    # --------------------------------------------------
                    # A rejected/revision plan becomes draft again
                    # --------------------------------------------------

                    if (
                        hasattr(
                            cad_file,
                            "process_plan_status",
                        )
                        and cad_file.process_plan_status
                        == "REJECTED"
                    ):

                        cad_file.process_plan_status = (
                            "DRAFT"
                        )

                        if hasattr(
                            cad_file,
                            "process_plan_remarks",
                        ):
                            cad_file.process_plan_remarks = None

                    update_fields = []

                    if hasattr(
                        cad_file,
                        "process_plan_created_by",
                    ):
                        update_fields.append(
                            "process_plan_created_by"
                        )

                    if hasattr(
                        cad_file,
                        "process_plan_status",
                    ):
                        update_fields.append(
                            "process_plan_status"
                        )

                    if hasattr(
                        cad_file,
                        "process_plan_remarks",
                    ):
                        update_fields.append(
                            "process_plan_remarks"
                        )

                    if update_fields:

                        cad_file.save(
                            update_fields=update_fields
                        )

                    return redirect(
                        "review_workload",
                        file_id=cad_file.id,
                    )

        # ======================================================
        # SAVE ENGINEERING INFORMATION
        # ======================================================

        elif action == "save_review":

            if plan_locked:

                return HttpResponseForbidden(
                    "This requirement has already been published to vendors."
                )

            form = EngineerReviewForm(
                request.POST,
                request.FILES,
                instance=cad_file,
            )

            # --------------------------------------------------
            # IMPORTANT
            #
            # Engineer must NOT directly control requirement
            # status from this form.
            #
            # Publishing is handled separately below.
            # --------------------------------------------------

            if "status" in form.fields:

                form.fields.pop(
                    "status"
                )

            if form.is_valid():

                form.save()

                return redirect(
                    "review_workload",
                    file_id=cad_file.id,
                )

        # ======================================================
        # PUBLISH TO VENDORS
        # ======================================================

        elif action == "publish":

            # --------------------------------------------------
            # Prevent accidental GET / invalid requests
            # --------------------------------------------------

            if plan_locked:

                return HttpResponseForbidden(
                    "This requirement has already been published to vendors."
                )

            # --------------------------------------------------
            # MANUFACTURING ROUTE REQUIRED
            # --------------------------------------------------

            processes = (
                RequirementProcess.objects
                .filter(
                    cad_model=cad_file,
                )
                .order_by(
                    "sequence",
                )
            )

            if not processes.exists():

                return render(
                    request,
                    "exchange/review.html",
                    {
                        "form": _review_form_without_status(
                            cad_file
                        ),
                        "process_form": _process_form(
                            cad_file
                        ),
                        "cad_file": cad_file,
                        "processes": processes,
                        "plan_locked": False,
                        "publish_error": (
                            "You cannot publish this requirement "
                            "until at least one manufacturing operation "
                            "has been defined."
                        ),
                    },
                )

            # --------------------------------------------------
            # PUBLISH
            # --------------------------------------------------

            with transaction.atomic():

                old_status = cad_file.status

                # ----------------------------------------------
                # Requirement becomes available to vendors
                # ----------------------------------------------

                cad_file.status = "PUBLISHED"

                # ----------------------------------------------
                # Engineering process plan becomes approved
                # ----------------------------------------------

                if hasattr(
                    cad_file,
                    "process_plan_status",
                ):
                    cad_file.process_plan_status = (
                        "APPROVED"
                    )

                if hasattr(
                    cad_file,
                    "process_plan_created_by",
                ):
                    cad_file.process_plan_created_by = (
                        cad_file.process_plan_created_by
                        or request.user
                    )

                if hasattr(
                    cad_file,
                    "process_plan_approved_by",
                ):
                    cad_file.process_plan_approved_by = (
                        request.user
                    )

                if hasattr(
                    cad_file,
                    "process_plan_approved_at",
                ):
                    cad_file.process_plan_approved_at = (
                        timezone.now()
                    )

                if hasattr(
                    cad_file,
                    "process_plan_submitted_at",
                ):
                    if not cad_file.process_plan_submitted_at:
                        cad_file.process_plan_submitted_at = (
                            timezone.now()
                        )

                # ----------------------------------------------
                # Save only fields that actually exist
                # ----------------------------------------------

                update_fields = [
                    "status",
                ]

                optional_fields = [
                    "process_plan_status",
                    "process_plan_created_by",
                    "process_plan_approved_by",
                    "process_plan_approved_at",
                    "process_plan_submitted_at",
                ]

                for field_name in optional_fields:

                    if hasattr(
                        cad_file,
                        field_name,
                    ):

                        update_fields.append(
                            field_name
                        )

                cad_file.save(
                    update_fields=update_fields
                )

                # ----------------------------------------------
                # Notify vendors
                # ----------------------------------------------

                if old_status != "PUBLISHED":

                    notify_requirement_published(
                        cad_file
                    )

            return redirect(
                "engineer_dashboard"
            )

        # ======================================================
        # UNKNOWN ACTION
        # ======================================================

        else:

            return HttpResponseBadRequest(
                "Invalid engineering action."
            )

    # ==========================================================
    # GET
    # ==========================================================

    form = _review_form_without_status(
        cad_file
    )

    process_form = _process_form(
        cad_file
    )

    return render(
        request,
        "exchange/review.html",
        {
            "form": form,
            "process_form": process_form,
            "cad_file": cad_file,
            "processes": processes,
            "plan_locked": plan_locked,
        },
    )


# ==============================================================
# REVIEW FORM HELPER
# ==============================================================


def _review_form_without_status(
    cad_file,
):

    form = EngineerReviewForm(
        instance=cad_file
    )

    if "status" in form.fields:

        form.fields.pop(
            "status"
        )

    return form


# ==============================================================
# PROCESS FORM HELPER
# ==============================================================


def _process_form(
    cad_file,
):

    next_sequence = (
        RequirementProcess.objects
        .filter(
            cad_model=cad_file,
        )
        .count()
        + 1
    )

    return EngineeringProcessForm(
        initial={
            "sequence": next_sequence,
            "quantity": cad_file.batch_quantity,
            "is_mandatory": True,
            "is_outsourcable": True,
        }
    )


# ==============================================================
# DIRECT RFQ & TARGETED SOURCING VIEWS
# ==============================================================

from datetime import timedelta
from django.contrib import messages
from users.models import User

@login_required
def oem_direct_rfq_bids(request, file_id):
    """OEM dashboard page to view vendor bids on Direct RFQ and directly award order."""
    job = get_object_or_404(CADModel, id=file_id)

    is_owner = request.user == job.uploaded_by
    is_staff = request.user.is_superuser or request.user.role == "ENGINEER"

    if not (is_owner or is_staff):
        return HttpResponseForbidden("Security Block: Access restricted to requirement owner.")

    bids = job.bids.select_related("vendor", "vendor__vendor_profile").order_by("offered_price")

    return render(
        request,
        "exchange/oem_direct_rfq_bids.html",
        {
            "job": job,
            "bids": bids,
        },
    )


@login_required
def oem_award_direct_vendor(request, file_id, bid_id):
    """Direct award action triggered by OEM for a specific vendor bid on Direct RFQ."""
    from ..models import Bid
    from ..services.notifications import notify_vendor_final_award

    job = get_object_or_404(CADModel, id=file_id)
    bid = get_object_or_404(Bid, id=bid_id, cad_model=job)

    is_owner = request.user == job.uploaded_by
    is_staff = request.user.is_superuser or request.user.role == "ENGINEER"

    if not (is_owner or is_staff):
        return HttpResponseForbidden("Security Block: Access restricted to requirement owner.")

    if request.method == "POST":
        job.selected_vendor = bid.vendor
        job.accepted_bid = bid
        job.accepted_vendor_cost = bid.offered_price
        job.final_primexa_quote = bid.offered_price
        job.status = "ASSIGNED_TO_VENDOR"
        job.vendor_committed_delivery_date = timezone.now().date() + timedelta(days=bid.delivery_days)
        job.vendor_awarded_at = timezone.now()
        job.save()

        notify_vendor_final_award(job)

        company_name = bid.vendor.company_name or bid.vendor.username
        messages.success(request, f"Order successfully awarded directly to vendor '{company_name}'!")
        return redirect("oem_dashboard")

    return redirect("oem_direct_rfq_bids", file_id=job.id)


@login_required
def engineer_bulk_invite_vendors(request, file_id):
    """Primexa Engineer action to bulk invite all or selected vendors to an RFQ."""
    if not (request.user.is_superuser or request.user.role == "ENGINEER"):
        return HttpResponseForbidden("Security Block: Primexa staff engineer access required.")

    job = get_object_or_404(CADModel, id=file_id)

    if request.method == "POST":
        invite_all = request.POST.get("invite_all") == "1"
        vendor_ids = request.POST.getlist("vendor_ids")

        verified_vendors = User.objects.filter(role="VENDOR", vendor_profile__is_verified=True)

        if invite_all:
            job.targeted_vendors.set(verified_vendors)
            count = verified_vendors.count()
            messages.success(request, f"Sent RFQ invitations to ALL {count} verified vendors in the network.")
        elif vendor_ids:
            selected_vendors = verified_vendors.filter(id__in=vendor_ids)
            job.targeted_vendors.add(*selected_vendors)
            count = selected_vendors.count()
            messages.success(request, f"Sent RFQ invitations to {count} selected vendors.")
        else:
            messages.warning(request, "No vendors were selected for invitation.")
            return redirect("review_workload", file_id=job.id)

        if job.status == "PENDING":
            job.status = "PUBLISHED"
            job.save(update_fields=["status"])

        for v in job.targeted_vendors.all():
            notify_requirement_published(job, recipient=v)

        return redirect("review_workload", file_id=job.id)

    return redirect("review_workload", file_id=job.id)


@login_required
def resend_bidding_notification(request, file_id):
    """Staff Engineers can resend RFQ / bidding notification emails for a requirement."""
    if not (request.user.is_superuser or request.user.role == "ENGINEER"):
        return HttpResponseForbidden("Security Block: Primexa staff engineer access required.")

    job = get_object_or_404(CADModel, id=file_id)
    notifications = notify_requirement_published(job)
    sent_count = len([n for n in notifications if n and n.status == "SENT"]) if notifications else 0

    messages.success(request, f"Bidding notification emails dispatched to network vendors (Sent: {sent_count}).")
    return redirect("engineer_dashboard")
