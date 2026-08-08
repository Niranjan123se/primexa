
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponseForbidden, HttpResponse
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from .models import CADModel, WorkloadTransfer, Bid
from .forms import EngineerReviewForm, CADUploadForm, BidForm
from .utils import generate_nda_pdf
from users.models import User


@login_required
def dashboard(request):
    if request.user.is_superuser or request.user.role == "ENGINEER":
        return redirect("engineer_dashboard")

    if request.user.role == "OEM":
        return redirect("oem_dashboard")

    if request.user.role == "VENDOR":
        return redirect("vendor_dashboard")

    return redirect("login")


@login_required
def oem_dashboard(request):
    jobs = CADModel.objects.filter(
        uploaded_by=request.user
    ).order_by("-uploaded_at")

    return render(
        request,
        "exchange/oem_dashboard.html",
        {"jobs": jobs}
    )


@login_required
def vendor_dashboard(request):
    jobs = CADModel.objects.filter(
        status__in=[
            "PUBLISHED",
            "BID_PLACED",
            "REVIEWED_SHORTLISTED"
        ]
    ).order_by("-uploaded_at")

    return render(
        request,
        "exchange/vendor_dashboard.html",
        {"jobs": jobs}
    )


@login_required
def engineer_dashboard(request):
    if request.user.role != "ENGINEER" and not request.user.is_superuser:
        return HttpResponseForbidden(
            "Security Block: Restricted to Primexa staff engineers."
        )

    jobs = CADModel.objects.all().order_by("-uploaded_at")

    return render(
        request,
        "exchange/engineer_dashboard.html",
        {"jobs": jobs}
    )


@login_required
def upload_job_view(request):
    if request.user.role != "OEM" and not request.user.is_superuser:
        return HttpResponseForbidden(
            "Only OEM users can upload requirements."
        )

    if request.method == "POST":
        form = CADUploadForm(request.POST, request.FILES)

        if form.is_valid():
            job = form.save(commit=False)
            job.uploaded_by = request.user
            job.save()

            return redirect("oem_dashboard")
    else:
        form = CADUploadForm()

    return render(
        request,
        "exchange/upload_job.html",
        {"form": form}
    )


@login_required
def sign_nda(request, file_id):
    cad_file = get_object_or_404(
        CADModel,
        id=file_id
    )

    if request.user.role != "VENDOR" and not request.user.is_superuser:
        return HttpResponseForbidden(
            "Only vendors can sign the NDA."
        )

    transfer, created = WorkloadTransfer.objects.get_or_create(
        cad_model=cad_file,
        sub_vendor=request.user
    )

    if request.method == "POST":
        transfer.nda_signed_by_sub = True
        transfer.agreed_at = timezone.now()

        x_forwarded_for = request.META.get(
            "HTTP_X_FORWARDED_FOR"
        )

        if x_forwarded_for:
            transfer.ip_address = (
                x_forwarded_for.split(",")[0].strip()
            )
        else:
            transfer.ip_address = request.META.get(
                "REMOTE_ADDR"
            )

        transfer.save()

        return redirect("vendor_dashboard")

    return render(
        request,
        "exchange/nda_sign.html",
        {
            "cad_file": cad_file,
            "transfer": transfer
        }
    )


@login_required
def download_file(request, file_id):
    cad_file = get_object_or_404(
        CADModel,
        id=file_id
    )

    if (
        request.user == cad_file.uploaded_by
        or request.user.role == "ENGINEER"
        or request.user.is_superuser
    ):
        return FileResponse(
            cad_file.file.open("rb"),
            as_attachment=True
        )

    has_signed = WorkloadTransfer.objects.filter(
        cad_model=cad_file,
        sub_vendor=request.user,
        nda_signed_by_sub=True
    ).exists()

    if has_signed:
        return FileResponse(
            cad_file.file.open("rb"),
            as_attachment=True
        )

    return HttpResponseForbidden(
        "Security Block: You must sign the NDA to download this file."
    )


@login_required
def download_nda_pdf(request, file_id):
    cad_file = get_object_or_404(
        CADModel,
        id=file_id
    )

    if (
        request.user.role == "ENGINEER"
        or request.user.is_superuser
    ):
        vendor_id = request.GET.get("vendor_id")

        if vendor_id:
            transfer = get_object_or_404(
                WorkloadTransfer,
                cad_model=cad_file,
                sub_vendor_id=vendor_id,
                nda_signed_by_sub=True
            )
        else:
            transfer = WorkloadTransfer.objects.filter(
                cad_model=cad_file,
                nda_signed_by_sub=True
            ).first()

            if not transfer:
                return HttpResponseForbidden(
                    "No signed NDA found for this workload yet."
                )

    else:
        transfer = get_object_or_404(
            WorkloadTransfer,
            cad_model=cad_file,
            sub_vendor=request.user,
            nda_signed_by_sub=True
        )

    pdf_buffer = generate_nda_pdf(transfer)

    response = HttpResponse(
        pdf_buffer.getvalue(),
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'attachment; '
        f'filename="Primexa_Legal_NDA_'
        f'{cad_file.tracking_number}_'
        f'{transfer.sub_vendor.username}.pdf"'
    )

    return response


@login_required
def review_workload(request, file_id):
    if request.user.role != "ENGINEER" and not request.user.is_superuser:
        return HttpResponseForbidden(
            "Security Block: Only Primexa staff engineers can view this."
        )

    cad_file = get_object_or_404(
        CADModel,
        id=file_id
    )

    if request.method == "POST":
        old_status = cad_file.status

        form = EngineerReviewForm(
            request.POST,
            request.FILES,
            instance=cad_file
        )

        if form.is_valid():
            updated_file = form.save()

            if (
                old_status == "PENDING"
                and updated_file.status == "PUBLISHED"
            ):
                vendors = User.objects.filter(
                    role="VENDOR"
                )

                vendor_emails = [
                    vendor.email
                    for vendor in vendors
                    if vendor.email
                ]

                if vendor_emails:
                    send_mail(
                        subject=(
                            f"New Workload Published: "
                            f"{updated_file.title} "
                            f"({updated_file.tracking_number})"
                        ),
                        message=(
                            "Hello Vendors,\n\n"
                            "A new manufacturing requirement has "
                            "been published on the Primexa Exchange.\n\n"
                            f"Tracking Number: "
                            f"{updated_file.tracking_number}\n"
                            f"Title: {updated_file.title}\n"
                            f"Batch Quantity: "
                            f"{updated_file.batch_quantity}\n\n"
                            "Log in to your dashboard to review "
                            "the requirement, sign the NDA and "
                            "submit your confidential quote."
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=vendor_emails,
                        fail_silently=False
                    )

            return redirect("engineer_dashboard")

    else:
        form = EngineerReviewForm(
            instance=cad_file
        )

    return render(
        request,
        "exchange/review.html",
        {
            "form": form,
            "cad_file": cad_file
        }
    )


@login_required
def place_bid_view(request, file_id):
    if request.user.role != "VENDOR" and not request.user.is_superuser:
        return HttpResponseForbidden(
            "Security Block: Only verified vendors can place bids."
        )

    cad_file = get_object_or_404(
        CADModel,
        id=file_id
    )

    has_signed = WorkloadTransfer.objects.filter(
        cad_model=cad_file,
        sub_vendor=request.user,
        nda_signed_by_sub=True
    ).exists()

    if not has_signed and not request.user.is_superuser:
        return redirect(
            "sign_nda",
            file_id=cad_file.id
        )

    if request.method == "POST":
        form = BidForm(request.POST)

        if form.is_valid():
            bid = form.save(commit=False)
            bid.cad_model = cad_file
            bid.vendor = request.user
            bid.save()

            if cad_file.status in [
                "PENDING",
                "PUBLISHED"
            ]:
                cad_file.status = "BID_PLACED"
                cad_file.save()

            return redirect("vendor_dashboard")

    else:
        form = BidForm()

    return render(
        request,
        "exchange/place_bid.html",
        {
            "form": form,
            "cad_file": cad_file
        }
    )


@login_required
def primexa_manage_bids(request, file_id):
    if request.user.role != "ENGINEER" and not request.user.is_superuser:
        return HttpResponseForbidden(
            "Security Block: Restricted to Primexa staff engineers."
        )

    cad_file = get_object_or_404(
        CADModel,
        id=file_id
    )

    bids = cad_file.bids.all().order_by(
        "offered_price"
    )

    if request.method == "POST":

        winning_bid_id = request.POST.get(
            "winning_bid_id"
        )

        try:
            margin_pct = float(
                request.POST.get(
                    "margin_percentage",
                    15.0
                )
            )
        except (TypeError, ValueError):
            margin_pct = 15.0

        winning_bid = get_object_or_404(
            Bid,
            id=winning_bid_id,
            cad_model=cad_file
        )

        vendor_cost = float(
            winning_bid.offered_price
        )

        primexa_quote = vendor_cost * (
            1 + margin_pct / 100.0
        )

        # -------------------------------------------------
        # STORE COMMERCIAL PROPOSAL
        # -------------------------------------------------

        cad_file.selected_vendor = winning_bid.vendor

        cad_file.accepted_vendor_cost = vendor_cost

        cad_file.platform_margin_percentage = margin_pct

        cad_file.final_primexa_quote = primexa_quote

        # IMPORTANT:
        # Vendor is NOT awarded yet.
        # OEM approval is required first.

        cad_file.status = "OEM_APPROVAL_PENDING"

        cad_file.save()

        # -------------------------------------------------
        # SEND COMMERCIAL PROPOSAL TO OEM
        # -------------------------------------------------

        if cad_file.uploaded_by.email:

            send_mail(
                subject=(
                    f"[Primexa Approval Required] "
                    f"Commercial Quote - "
                    f"{cad_file.tracking_number}"
                ),

                message=(
                    "Dear OEM Partner,\n\n"

                    "Primexa has completed the vendor evaluation "
                    "for your manufacturing requirement.\n\n"

                    f"Requirement: {cad_file.title}\n"

                    f"Tracking Number: "
                    f"{cad_file.tracking_number}\n\n"

                    f"Final Commercial Quote from Primexa: "
                    f"INR {primexa_quote:.2f}\n\n"

                    f"Estimated Delivery: "
                    f"{winning_bid.delivery_days} Days\n\n"

                    "The above quotation includes the applicable "
                    "Primexa platform/service margin and the "
                    "selected manufacturing partner's commercial "
                    "cost.\n\n"

                    "Please review and approve the commercial "
                    "proposal through the Primexa platform.\n\n"

                    "IMPORTANT:\n"
                    "The manufacturing vendor will NOT receive "
                    "the final award until OEM approval is received.\n\n"

                    "Regards,\n"
                    "Primexa Global"
                ),

                from_email=settings.DEFAULT_FROM_EMAIL,

                recipient_list=[
                    cad_file.uploaded_by.email
                ],

                fail_silently=True
            )

        return redirect(
            "engineer_dashboard"
        )

    return render(
        request,
        "exchange/primexa_manage_bids.html",
        {
            "cad_file": cad_file,
            "bids": bids
        }
    )
@login_required
def oem_approve_quote(request, file_id):


    cad_file = get_object_or_404(
        CADModel,
        id=file_id
    )

    # Only the OEM who uploaded this requirement
    # can approve the commercial quote.

    if (
        request.user != cad_file.uploaded_by
        and not request.user.is_superuser
    ):
        return HttpResponseForbidden(
            "Security Block: Only the requesting OEM can approve this quote."
        )

    if cad_file.status != "OEM_APPROVAL_PENDING":
        return HttpResponseForbidden(
            "This commercial quote is not currently awaiting OEM approval."
        )

    if request.method == "POST":

        approval = request.POST.get(
            "approval"
        )

        remarks = request.POST.get(
            "approval_remarks",
            ""
        ).strip()

        if approval == "APPROVE":

            cad_file.status = "OEM_APPROVED"

            cad_file.oem_approval_at = timezone.now()

            cad_file.oem_approval_remarks = remarks

            cad_file.oem_approved_by = request.user

            cad_file.save()

            return redirect(
                "oem_dashboard"
            )

        elif approval == "REJECT":

            cad_file.status = "OEM_REJECTED"

            cad_file.oem_approval_at = timezone.now()

            cad_file.oem_approval_remarks = remarks

            cad_file.oem_approved_by = request.user

            cad_file.save()

            return redirect(
                "oem_dashboard"
            )

    return render(
        request,
        "exchange/oem_approve_quote.html",
        {
            "cad_file": cad_file
        }
    )
@login_required
def final_vendor_award(request, file_id):
    if request.user.role != "ENGINEER" and not request.user.is_superuser:
        return HttpResponseForbidden(
            "Security Block: Only Primexa staff engineers can issue the final award."
        )

    cad_file = get_object_or_404(
        CADModel,
        id=file_id
    )

    if cad_file.status != "OEM_APPROVED":
        return HttpResponseForbidden(
            "Final vendor award is only available after OEM approval."
        )

    if not cad_file.selected_vendor:
        return HttpResponseForbidden(
            "No vendor has been selected for this requirement."
        )

    if request.method == "POST":

        cad_file.status = "VENDOR_AWARDED"

        cad_file.save()

        vendor = cad_file.selected_vendor

        if vendor.email:

            send_mail(
                subject=(
                    f"[Primexa Final Award] "
                    f"Work Order - "
                    f"{cad_file.tracking_number}"
                ),
                message=(
                    "Hello Workshop Partner,\n\n"

                    "Primexa is pleased to confirm that "
                    "the OEM has approved the commercial proposal "
                    "for the following manufacturing requirement.\n\n"

                    f"Requirement: {cad_file.title}\n"
                    f"Tracking Number: {cad_file.tracking_number}\n"
                    f"Approved Commercial Value: "
                    f"INR {cad_file.final_primexa_quote:.2f}\n\n"

                    "You have now received the final manufacturing award.\n\n"

                    "Primexa will coordinate the next stages of "
                    "production, quality assurance and delivery.\n\n"

                    "Regards,\n"
                    "Primexa Global"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[vendor.email],
                fail_silently=True
            )

        return redirect(
            "engineer_dashboard"
        )

    return render(
        request,
        "exchange/final_vendor_award.html",
        {
            "cad_file": cad_file
        }
    )
