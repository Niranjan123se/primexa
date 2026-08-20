from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ..forms import (
    FAIReviewForm,
    FAISubmissionForm,
)
from ..models import (
    CADModel,
    FAIRecord,
)
from ..services.notifications import (
    notify_fai_rejected,
)


@login_required
def fai_submit(request, file_id):
    # ======================================================
    # ACCESS CONTROL
    # ======================================================

    if (
        request.user.role != "VENDOR"
        and not request.user.is_superuser
    ):
        return HttpResponseForbidden(
            "Security Block: Only the awarded vendor can submit FAI."
        )

    cad_file = get_object_or_404(
        CADModel,
        id=file_id,
    )

    # ======================================================
    # ONLY AWARDED / ONBOARDED VENDOR
    # ======================================================

    if cad_file.selected_vendor != request.user:
        return HttpResponseForbidden(
            "Security Block: You are not the selected vendor for this requirement."
        )

    if cad_file.status not in [
        "VENDOR_AWARDED",
        "FINAL_VENDOR_ONBOARDED",
        "FAI_PENDING",
    ]:
        return HttpResponseForbidden(
            "FAI submission is not currently available for this requirement."
        )

    # ======================================================
    # GET / CREATE FAI RECORD
    # ======================================================

    fai_record, created = (
        FAIRecord.objects.get_or_create(
            cad_model=cad_file,
            vendor=request.user,
        )
    )

    # ======================================================
    # SUBMIT FAI
    # ======================================================

    if request.method == "POST":
        form = FAISubmissionForm(
            request.POST,
            request.FILES,
            instance=fai_record,
        )

        if form.is_valid():
            record = form.save(
                commit=False,
            )

            record.cad_model = cad_file
            record.vendor = request.user

            # --------------------------------------------------
            # FAI submitted for engineering review
            # --------------------------------------------------

            record.status = "SUBMITTED"

            if hasattr(
                record,
                "submitted_at",
            ):
                record.submitted_at = (
                    timezone.now()
                )

            record.save()

            # --------------------------------------------------
            # Update requirement status
            # --------------------------------------------------

            cad_file.status = "FAI_PENDING"

            cad_file.save(
                update_fields=[
                    "status",
                ]
            )

            return redirect(
                "vendor_dashboard"
            )

    else:
        form = FAISubmissionForm(
            instance=fai_record,
        )

    return render(
        request,
        "exchange/fai_submit.html",
        {
            "form": form,
            "cad_file": cad_file,
            "fai_record": fai_record,
        },
    )


@login_required
def fai_review(request, file_id):
    # ======================================================
    # ENGINEER ACCESS ONLY
    # ======================================================

    if (
        request.user.role != "ENGINEER"
        and not request.user.is_superuser
    ):
        return HttpResponseForbidden(
            "Security Block: Only Primexa staff engineers can review FAI."
        )

    cad_file = get_object_or_404(
        CADModel,
        id=file_id,
    )

    # ======================================================
    # GET LATEST FAI RECORD
    # ======================================================

    fai_record = (
        FAIRecord.objects
        .filter(
            cad_model=cad_file,
        )
        .order_by(
            "-created_at",
        )
        .first()
    )

    if not fai_record:
        return HttpResponseForbidden(
            "No FAI submission exists for this requirement."
        )

    # ======================================================
    # REVIEW
    # ======================================================

    if request.method == "POST":
        form = FAIReviewForm(
            request.POST,
            instance=fai_record,
        )

        if form.is_valid():
            record = form.save(
                commit=False,
            )

            # --------------------------------------------------
            # APPROVED
            # --------------------------------------------------

            if record.status == "APPROVED":
                if hasattr(
                    record,
                    "reviewed_at",
                ):
                    record.reviewed_at = (
                        timezone.now()
                    )

                if hasattr(
                    record,
                    "reviewed_by",
                ):
                    record.reviewed_by = (
                        request.user
                    )

                record.save()

                cad_file.status = (
                    "FAI_APPROVED"
                )

                cad_file.save(
                    update_fields=[
                        "status",
                    ]
                )

            # --------------------------------------------------
            # REJECTED
            # --------------------------------------------------

            elif record.status == "REJECTED":
                if hasattr(
                    record,
                    "reviewed_at",
                ):
                    record.reviewed_at = (
                        timezone.now()
                    )

                if hasattr(
                    record,
                    "reviewed_by",
                ):
                    record.reviewed_by = (
                        request.user
                    )

                record.save()

                # Rejected FAI goes back to pending
                # so vendor can correct and resubmit.

                cad_file.status = (
                    "FAI_PENDING"
                )

                cad_file.save(
                    update_fields=[
                        "status",
                    ]
                )
                # ======================================================
                # NOTIFY VENDOR
                # ======================================================

                notify_fai_rejected(
                    fai_record=record,
                    remarks=record.engineer_remarks or "",
                )

            return redirect(
                "engineer_dashboard"
            )

    else:
        form = FAIReviewForm(
            instance=fai_record,
        )

    return render(
        request,
        "exchange/fai_review.html",
        {
            "form": form,
            "cad_file": cad_file,
            "fai_record": fai_record,
        },
    )