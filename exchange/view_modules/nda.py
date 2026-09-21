from django.contrib.auth.decorators import login_required
from django.http import (
FileResponse,
HttpResponse,
HttpResponseForbidden,
)
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ..models import (
CADModel,
WorkloadTransfer,
)

from ..utils import generate_nda_pdf

@login_required
def sign_nda(request, file_id):
    cad_file = get_object_or_404(
        CADModel,
        id=file_id,
    )

    if (
        request.user.role != "VENDOR"
        and not request.user.is_superuser
    ):
        return HttpResponseForbidden(
            "Only vendors can sign the NDA."
        )

    if cad_file.targeted_vendors.exists() and not (
        request.user.is_superuser
        or request.user.role == "ENGINEER"
        or cad_file.targeted_vendors.filter(id=request.user.id).exists()
    ):
        return HttpResponseForbidden("Security Block: You are not authorized to sign NDA for this targeted RFQ.")

    transfer, created = (
        WorkloadTransfer.objects.get_or_create(
            cad_model=cad_file,
            sub_vendor=request.user,
        )
    )

    if request.method == "POST":

        transfer.nda_signed_by_sub = True
        transfer.agreed_at = timezone.now()

        x_forwarded_for = request.META.get(
            "HTTP_X_FORWARDED_FOR"
        )

        if x_forwarded_for:

            transfer.ip_address = (
                x_forwarded_for
                .split(",")[0]
                .strip()
            )

        else:

            transfer.ip_address = (
                request.META.get(
                    "REMOTE_ADDR"
                )
            )

        transfer.save()

        return redirect(
            "vendor_dashboard"
        )

    return render(
        request,
        "exchange/nda_sign.html",
        {
            "cad_file": cad_file,
            "transfer": transfer,
        },
    )


@login_required
def download_file(request, file_id):
    cad_file = get_object_or_404(
        CADModel,
        id=file_id,
    )

    if request.user == cad_file.uploaded_by:

        if not cad_file.file:
            return HttpResponseForbidden(
                "No CAD file is available for this requirement."
            )

        return FileResponse(
            cad_file.file.open("rb"),
            as_attachment=True,
        )

    if (
        request.user.role == "ENGINEER"
        or request.user.is_superuser
    ):

        if not cad_file.file:
            return HttpResponseForbidden(
                "No CAD file is available for this requirement."
            )

        return FileResponse(
            cad_file.file.open("rb"),
            as_attachment=True,
        )

    has_signed = (
        WorkloadTransfer.objects
        .filter(
            cad_model=cad_file,
            sub_vendor=request.user,
            nda_signed_by_sub=True,
        )
        .exists()
    )

    if has_signed:

        if not cad_file.file:
            return HttpResponseForbidden(
                "No CAD file is available for this requirement."
            )

        return FileResponse(
            cad_file.file.open("rb"),
            as_attachment=True,
        )

    return HttpResponseForbidden(
        "Security Block: You must sign the NDA to download this file."
    )

@login_required
def download_nda_pdf(request, file_id):
    cad_file = get_object_or_404(
        CADModel,
        id=file_id,
    )

    if (
        request.user.role == "ENGINEER"
        or request.user.is_superuser
    ):

        vendor_id = request.GET.get(
            "vendor_id"
        )

        if vendor_id:

            transfer = get_object_or_404(
                WorkloadTransfer,
                cad_model=cad_file,
                sub_vendor_id=vendor_id,
                nda_signed_by_sub=True,
            )

        else:

            transfer = (
                WorkloadTransfer.objects
                .filter(
                    cad_model=cad_file,
                    nda_signed_by_sub=True,
                )
                .first()
            )

            if not transfer:

                return HttpResponseForbidden(
                    "No signed NDA found for this workload yet."
                )

    else:

        transfer = get_object_or_404(
            WorkloadTransfer,
            cad_model=cad_file,
            sub_vendor=request.user,
            nda_signed_by_sub=True,
        )

    pdf_buffer = generate_nda_pdf(
        transfer
    )

    response = HttpResponse(
        pdf_buffer.getvalue(),
        content_type="application/pdf",
    )

    response["Content-Disposition"] = (
        "attachment; "
        f'filename="Primexa_Legal_NDA_'
        f'{cad_file.tracking_number}_'
        f'{transfer.sub_vendor.username}.pdf"'
    )

    return response
