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

from ..forms.engineering_process import (
    EngineeringProcessForm,
    EngineeringProcessReviewForm,
)

from ..models import (
    CADModel,
    RequirementProcess,
)


# ==============================================================
# ENGINEERING PROCESS PLAN
# ==============================================================


@login_required
def engineering_process_plan(
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
            "Only Primexa engineers can manage engineering process plans."
        )

    # ----------------------------------------------------------
    # REQUIREMENT
    # ----------------------------------------------------------

    cad_file = get_object_or_404(
        CADModel,
        id=file_id,
    )

    # ----------------------------------------------------------
    # EXISTING PROCESSES
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
    # CHECK IF PLAN IS LOCKED
    # ----------------------------------------------------------

    plan_locked = cad_file.process_plan_status in [
        "SUBMITTED",
        "APPROVED",
    ]

    # ----------------------------------------------------------
    # ADD PROCESS
    # ----------------------------------------------------------

    if request.method == "POST":

        if plan_locked:

            return HttpResponseForbidden(
                "This process plan is locked. "
                "It must be rejected before it can be edited."
            )

        form = EngineeringProcessForm(
            request.POST,
        )

        if form.is_valid():

            sequence = form.cleaned_data[
                "sequence"
            ]

            duplicate = (
                RequirementProcess.objects
                .filter(
                    cad_model=cad_file,
                    sequence=sequence,
                )
                .exists()
            )

            if duplicate:

                form.add_error(
                    "sequence",
                    (
                        "This sequence number already exists "
                        "for this requirement."
                    ),
                )

            else:

                process = form.save(
                    commit=False,
                )

                process.cad_model = cad_file

                process.save()

                # --------------------------------------------------
                # Process plan belongs to engineer
                # --------------------------------------------------

                if not cad_file.process_plan_created_by:

                    cad_file.process_plan_created_by = (
                        request.user
                    )

                # --------------------------------------------------
                # Rejected plan becomes draft after editing
                # --------------------------------------------------

                if cad_file.process_plan_status == "REJECTED":

                    cad_file.process_plan_status = "DRAFT"

                    cad_file.process_plan_remarks = None

                    cad_file.process_plan_approved_by = None

                    cad_file.process_plan_approved_at = None

                cad_file.save(
                    update_fields=[
                        "process_plan_created_by",
                        "process_plan_status",
                        "process_plan_remarks",
                        "process_plan_approved_by",
                        "process_plan_approved_at",
                    ]
                )

                return redirect(
                    "engineering_process_plan",
                    file_id=cad_file.id,
                )

    else:

        next_sequence = (
            processes.count() + 1
        )

        form = EngineeringProcessForm(
            initial={
                "sequence": next_sequence,
                "quantity": cad_file.batch_quantity,
                "is_mandatory": True,
                "is_outsourcable": True,
            }
        )

    return render(
        request,
        "exchange/engineering_process_plan.html",
        {
            "cad_file": cad_file,
            "processes": processes,
            "form": form,
            "plan_locked": plan_locked,
        },
    )


# ==============================================================
# SUBMIT PROCESS PLAN FOR APPROVAL
# ==============================================================


@login_required
def submit_engineering_process_plan(
    request,
    file_id,
):

    if (
        request.user.role != "ENGINEER"
        and not request.user.is_superuser
    ):
        return HttpResponseForbidden(
            "Only Primexa engineers can submit process plans."
        )

    if request.method != "POST":

        return HttpResponseBadRequest(
            "Process plan submission must use POST."
        )

    cad_file = get_object_or_404(
        CADModel,
        id=file_id,
    )

    processes_exist = (
        RequirementProcess.objects
        .filter(
            cad_model=cad_file,
        )
        .exists()
    )

    if not processes_exist:

        return HttpResponseForbidden(
            "Cannot submit an empty process plan."
        )

    if cad_file.process_plan_status == "APPROVED":

        return HttpResponseForbidden(
            "This process plan has already been approved."
        )

    cad_file.process_plan_created_by = (
        cad_file.process_plan_created_by
        or request.user
    )

    cad_file.process_plan_status = "SUBMITTED"

    cad_file.process_plan_submitted_at = (
        timezone.now()
    )

    cad_file.process_plan_approved_by = None

    cad_file.process_plan_approved_at = None

    cad_file.save(
        update_fields=[
            "process_plan_created_by",
            "process_plan_status",
            "process_plan_submitted_at",
            "process_plan_approved_by",
            "process_plan_approved_at",
        ]
    )

    return redirect(
        "engineering_process_plan",
        file_id=cad_file.id,
    )


# ==============================================================
# REVIEW PROCESS PLAN
# ==============================================================


@login_required
def review_engineering_process_plan(
    request,
    file_id,
):

    if (
        request.user.role != "ENGINEER"
        and not request.user.is_superuser
    ):
        return HttpResponseForbidden(
            "Only Primexa engineers can review process plans."
        )

    cad_file = get_object_or_404(
        CADModel,
        id=file_id,
    )

    processes = (
        RequirementProcess.objects
        .filter(
            cad_model=cad_file,
        )
        .order_by(
            "sequence",
        )
    )

    if request.method == "POST":

        form = EngineeringProcessReviewForm(
            request.POST,
        )

        if form.is_valid():

            decision = form.cleaned_data[
                "decision"
            ]

            remarks = form.cleaned_data[
                "remarks"
            ]

            # --------------------------------------------------
            # APPROVE
            # --------------------------------------------------

            if decision == "APPROVE":

                if not processes.exists():

                    form.add_error(
                        None,
                        (
                            "Cannot approve an empty "
                            "engineering process plan."
                        ),
                    )

                else:

                    cad_file.process_plan_status = (
                        "APPROVED"
                    )

                    cad_file.process_plan_approved_by = (
                        request.user
                    )

                    cad_file.process_plan_approved_at = (
                        timezone.now()
                    )

                    cad_file.process_plan_remarks = (
                        remarks
                    )

                    cad_file.save(
                        update_fields=[
                            "process_plan_status",
                            "process_plan_approved_by",
                            "process_plan_approved_at",
                            "process_plan_remarks",
                        ]
                    )

                    return redirect(
                        "engineer_dashboard"
                    )

            # --------------------------------------------------
            # REJECT
            # --------------------------------------------------

            elif decision == "REJECT":

                if not remarks:

                    form.add_error(
                        "remarks",
                        (
                            "Please provide engineering "
                            "remarks explaining the rejection."
                        ),
                    )

                else:

                    cad_file.process_plan_status = (
                        "REJECTED"
                    )

                    cad_file.process_plan_approved_by = None

                    cad_file.process_plan_approved_at = None

                    cad_file.process_plan_remarks = (
                        remarks
                    )

                    cad_file.save(
                        update_fields=[
                            "process_plan_status",
                            "process_plan_approved_by",
                            "process_plan_approved_at",
                            "process_plan_remarks",
                        ]
                    )

                    return redirect(
                        "engineering_process_plan",
                        file_id=cad_file.id,
                    )

    else:

        form = EngineeringProcessReviewForm()

    return render(
        request,
        "exchange/engineering_process_review.html",
        {
            "cad_file": cad_file,
            "processes": processes,
            "form": form,
        },
    )


# ==============================================================
# DELETE PROCESS
# ==============================================================


@login_required
def delete_engineering_process(
    request,
    process_id,
):

    if (
        request.user.role != "ENGINEER"
        and not request.user.is_superuser
    ):
        return HttpResponseForbidden(
            "Only Primexa engineers can modify process plans."
        )

    if request.method != "POST":

        return HttpResponseBadRequest(
            "Process deletion must use POST."
        )

    process = get_object_or_404(
        RequirementProcess.objects.select_related(
            "cad_model",
        ),
        id=process_id,
    )

    cad_file = process.cad_model

    if cad_file.process_plan_status in [
        "SUBMITTED",
        "APPROVED",
    ]:

        return HttpResponseForbidden(
            "This process plan is locked."
        )

    process.delete()

    # ----------------------------------------------------------
    # Re-number sequence
    # ----------------------------------------------------------

    remaining = (
        RequirementProcess.objects
        .filter(
            cad_model=cad_file,
        )
        .order_by(
            "sequence",
        )
    )

    for index, item in enumerate(
        remaining,
        start=1,
    ):

        if item.sequence != index:

            item.sequence = index

            item.save(
                update_fields=[
                    "sequence",
                    "updated_at",
                ]
            )

    return redirect(
        "engineering_process_plan",
        file_id=cad_file.id,
    )