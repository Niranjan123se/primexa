from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from ..forms.process import RequirementProcessForm
from ..models import CADModel, RequirementProcess


# ==============================================================
# OEM REQUIREMENT PROCESS BUILDER
# ==============================================================


@login_required
def requirement_processes(request, file_id):
    """
    OEM Process Builder.

    Allows an OEM to define the manufacturing route for
    an existing CAD requirement.

    Example:

        1. CNC Turning
        2. VMC Milling
        3. Heat Treatment
        4. Surface Grinding
        5. Anodizing
    """

    # ----------------------------------------------------------
    # SECURITY
    # ----------------------------------------------------------

    if (
        request.user.role != "OEM"
        and not request.user.is_superuser
    ):
        return HttpResponseForbidden(
            "Only the OEM can define manufacturing processes."
        )

    # ----------------------------------------------------------
    # REQUIREMENT
    # ----------------------------------------------------------

    cad_file = get_object_or_404(
        CADModel,
        id=file_id,
    )

    # ----------------------------------------------------------
    # OWNERSHIP
    # ----------------------------------------------------------

    if (
        cad_file.uploaded_by != request.user
        and not request.user.is_superuser
    ):
        return HttpResponseForbidden(
            "You are not authorized to modify this requirement."
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
    # ADD PROCESS
    # ----------------------------------------------------------

    if request.method == "POST":

        form = RequirementProcessForm(
            request.POST,
        )

        if form.is_valid():

            sequence = form.cleaned_data[
                "sequence"
            ]

            # --------------------------------------------------
            # Prevent duplicate sequence numbers
            # --------------------------------------------------

            if RequirementProcess.objects.filter(
                cad_model=cad_file,
                sequence=sequence,
            ).exists():

                form.add_error(
                    "sequence",
                    (
                        "This process sequence already exists "
                        "for this requirement."
                    ),
                )

            else:

                process = form.save(
                    commit=False,
                )

                process.cad_model = cad_file

                process.save()

                return redirect(
                    "requirement_processes",
                    file_id=cad_file.id,
                )

    else:

        # ------------------------------------------------------
        # Automatically suggest next sequence
        # ------------------------------------------------------

        next_sequence = (
            processes.count() + 1
        )

        form = RequirementProcessForm(
            initial={
                "sequence": next_sequence,
                "quantity": cad_file.batch_quantity,
                "is_mandatory": True,
                "is_outsourcable": True,
            }
        )

    # ----------------------------------------------------------
    # RENDER
    # ----------------------------------------------------------

    return render(
        request,
        "exchange/requirement_processes.html",
        {
            "cad_file": cad_file,
            "processes": processes,
            "form": form,
        },
    )


# ==============================================================
# DELETE REQUIREMENT PROCESS
# ==============================================================


@login_required
def delete_requirement_process(
    request,
    process_id,
):
    """
    Delete one process from an OEM requirement.
    """

    # ----------------------------------------------------------
    # SECURITY
    # ----------------------------------------------------------

    if (
        request.user.role != "OEM"
        and not request.user.is_superuser
    ):
        return HttpResponseForbidden(
            "Only the OEM can remove manufacturing processes."
        )

    # ----------------------------------------------------------
    # PROCESS
    # ----------------------------------------------------------

    process = get_object_or_404(
        RequirementProcess.objects.select_related(
            "cad_model",
        ),
        id=process_id,
    )

    cad_file = process.cad_model

    # ----------------------------------------------------------
    # OWNERSHIP
    # ----------------------------------------------------------

    if (
        cad_file.uploaded_by != request.user
        and not request.user.is_superuser
    ):
        return HttpResponseForbidden(
            "You are not authorized to modify this requirement."
        )

    # ----------------------------------------------------------
    # ONLY POST ALLOWED
    # ----------------------------------------------------------

    if request.method != "POST":
        return HttpResponseBadRequest(
            "Process deletion must use POST."
        )

    # ----------------------------------------------------------
    # DELETE
    # ----------------------------------------------------------

    process.delete()

    # ----------------------------------------------------------
    # Re-number remaining processes
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
        "requirement_processes",
        file_id=cad_file.id,
    )