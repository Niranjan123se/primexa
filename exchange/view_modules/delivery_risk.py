from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone

from ..forms import DeliveryRiskForm
from ..models import (
    CADModel,
    DeliveryRiskAlert,
)


# ==============================================================
# REPORT DELIVERY RISK
# ==============================================================


@login_required
def report_delivery_risk(request, file_id):

    # ==========================================================
    # VENDOR SECURITY
    # ==========================================================

    if (
        request.user.role != "VENDOR"
        and not request.user.is_superuser
    ):
        return HttpResponseForbidden(
            "Only the awarded vendor can report delivery risk."
        )

    # ==========================================================
    # REQUIREMENT
    # ==========================================================

    cad_file = get_object_or_404(
        CADModel,
        id=file_id,
    )

    # ==========================================================
    # AWARDED VENDOR CHECK
    # ==========================================================

    if (
        not request.user.is_superuser
        and cad_file.selected_vendor_id
        != request.user.id
    ):
        return HttpResponseForbidden(
            "You are not the awarded vendor for this requirement."
        )

    # ==========================================================
    # ACTIVE AWARD CHECK
    # ==========================================================

    if cad_file.status not in [
        "VENDOR_AWARDED",
        "FINAL_VENDOR_ONBOARDED",
    ]:
        return HttpResponseForbidden(
            "Delivery risk can only be reported for an active award."
        )

    # ==========================================================
    # ORIGINAL DELIVERY COMMITMENT
    # ==========================================================

    original_delivery_date = (
        cad_file.vendor_committed_delivery_date
        or cad_file.expected_delivery_date
    )

    if not original_delivery_date:

        return HttpResponseForbidden(
            "No vendor delivery commitment has been recorded "
            "for this requirement."
        )

    # ==========================================================
    # PREVENT DUPLICATE ACTIVE ALERTS
    # ==========================================================

    existing_alert = (
        DeliveryRiskAlert.objects
        .filter(
            cad_model=cad_file,
            vendor=request.user,
            status__in=[
                "OPEN",
                "UNDER_REVIEW",
                "RECOVERY_REQUESTED",
            ],
        )
        .order_by("-reported_at")
        .first()
    )

    if existing_alert:

        return render(
            request,
            "exchange/delivery_risk_already_reported.html",
            {
                "cad_file": cad_file,
                "alert": existing_alert,
            },
        )

    # ==========================================================
    # POST
    # ==========================================================

    if request.method == "POST":

        form = DeliveryRiskForm(
            request.POST,
            request.FILES,
            original_delivery_date=(
                original_delivery_date
            ),
            maximum_quantity=(
                cad_file.batch_quantity
            ),
        )

        # ======================================================
        # VALIDATE FORM ONCE
        # ======================================================

        is_valid = form.is_valid()

        # ======================================================
        # DEVELOPMENT DIAGNOSTICS
        # ======================================================

        print("")
        print("==============================================")
        print("       DELIVERY RISK SUBMISSION")
        print("==============================================")
        print(
            "USER:",
            request.user.username,
        )
        print(
            "USER ID:",
            request.user.id,
        )
        print(
            "FILE ID:",
            cad_file.id,
        )
        print(
            "FILE TITLE:",
            cad_file.title,
        )
        print(
            "FILE STATUS:",
            cad_file.status,
        )
        print(
            "SELECTED VENDOR ID:",
            cad_file.selected_vendor_id,
        )
        print(
            "ORIGINAL DELIVERY DATE:",
            original_delivery_date,
        )
        print(
            "MAXIMUM QUANTITY:",
            cad_file.batch_quantity,
        )
        print(
            "FORM VALID:",
            is_valid,
        )
        print(
            "FORM ERRORS:",
            form.errors,
        )
        print(
            "POST DATA:",
            request.POST,
        )
        print(
            "FILES:",
            request.FILES,
        )
        print("==============================================")

        # ======================================================
        # INVALID FORM
        # ======================================================

        if not is_valid:

            print("")
            print("==============================================")
            print("DELIVERY RISK FORM VALIDATION FAILED")
            print("==============================================")
            print(
                form.errors.as_json()
            )
            print("==============================================")
            print("")

        # ======================================================
        # VALID FORM
        # ======================================================

        else:

            try:

                # --------------------------------------------------
                # CREATE ALERT WITHOUT SAVING YET
                # --------------------------------------------------

                alert = form.save(
                    commit=False
                )

                # --------------------------------------------------
                # ASSIGN REQUIREMENT
                # --------------------------------------------------

                alert.cad_model = cad_file

                # --------------------------------------------------
                # ASSIGN VENDOR
                # --------------------------------------------------

                alert.vendor = request.user

                # --------------------------------------------------
                # ORIGINAL DELIVERY COMMITMENT
                # --------------------------------------------------

                alert.original_delivery_date = (
                    original_delivery_date
                )

                # --------------------------------------------------
                # QUANTITY CALCULATION
                # --------------------------------------------------

                completed_quantity = (
                    alert.quantity_completed
                    or 0
                )

                alert.quantity_remaining = max(
                    cad_file.batch_quantity
                    - completed_quantity,
                    0,
                )

                # --------------------------------------------------
                # INITIAL STATUS
                # --------------------------------------------------

                alert.status = "OPEN"

                # ==================================================
                # BEFORE DATABASE SAVE
                # ==================================================

                print("")
                print("==============================================")
                print("ABOUT TO SAVE DELIVERY RISK ALERT")
                print("==============================================")
                print(
                    "CAD MODEL:",
                    alert.cad_model_id,
                )
                print(
                    "VENDOR:",
                    alert.vendor_id,
                )
                print(
                    "STATUS:",
                    alert.status,
                )
                print(
                    "ORIGINAL DELIVERY:",
                    alert.original_delivery_date,
                )
                print(
                    "REVISED DELIVERY:",
                    alert.revised_delivery_date,
                )
                print(
                    "QUANTITY COMPLETED:",
                    alert.quantity_completed,
                )
                print(
                    "QUANTITY REMAINING:",
                    alert.quantity_remaining,
                )
                print("==============================================")

                # ==================================================
                # SAVE
                # ==================================================

                alert.save()

                # ==================================================
                # AFTER DATABASE SAVE
                # ==================================================

                print("")
                print("==============================================")
                print("DELIVERY RISK ALERT SAVED SUCCESSFULLY")
                print("==============================================")
                print(
                    "ALERT ID:",
                    alert.id,
                )
                print(
                    "ALERT STATUS:",
                    alert.status,
                )
                print("==============================================")
                print("")

                # ==================================================
                # VERIFY DATABASE RECORD
                # ==================================================

                saved_alert = (
                    DeliveryRiskAlert.objects
                    .filter(
                        id=alert.id
                    )
                    .first()
                )

                print(
                    "DATABASE VERIFICATION:",
                    saved_alert is not None,
                )

                if saved_alert:

                    print(
                        "DATABASE STATUS:",
                        saved_alert.status,
                    )

                # ==================================================
                # NOTIFY ENGINEERING
                # ==================================================

                try:

                    from ..services.notifications import (
                        notify_delivery_risk,
                    )

                    notify_delivery_risk(
                        alert
                    )

                    print("")
                    print(
                        "DELIVERY RISK NOTIFICATION TRIGGERED"
                    )
                    print("")

                except Exception as notification_error:

                    # ------------------------------------------------
                    # Notification failure should NOT delete the
                    # delivery-risk alert.
                    # ------------------------------------------------

                    print("")
                    print("==============================================")
                    print("NOTIFICATION ERROR")
                    print("==============================================")
                    print(
                        type(
                            notification_error
                        ).__name__
                    )
                    print(
                        str(
                            notification_error
                        )
                    )
                    print("==============================================")
                    print("")

                # ==================================================
                # SUCCESS
                # ==================================================

                return redirect(
                    "vendor_dashboard"
                )

            except Exception as exc:

                # ==================================================
                # DATABASE / SAVE ERROR
                # ==================================================

                print("")
                print("==============================================")
                print("DELIVERY RISK SAVE ERROR")
                print("==============================================")
                print(
                    "ERROR TYPE:",
                    type(exc).__name__,
                )
                print(
                    "ERROR:",
                    str(exc),
                )
                print("==============================================")
                print("")

                form.add_error(
                    None,
                    (
                        "The delivery-risk alert could not be "
                        f"saved: {exc}"
                    ),
                )

    # ==========================================================
    # GET
    # ==========================================================

    else:

        form = DeliveryRiskForm(
            original_delivery_date=(
                original_delivery_date
            ),
            maximum_quantity=(
                cad_file.batch_quantity
            ),
        )

    # ==========================================================
    # RENDER
    # ==========================================================

    return render(
        request,
        "exchange/report_delivery_risk.html",
        {
            "form": form,
            "cad_file": cad_file,
            "original_delivery_date": (
                original_delivery_date
            ),
        },
    )


# ==============================================================
# REVIEW DELIVERY RISK
# ==============================================================


@login_required
def review_delivery_risk(
    request,
    alert_id,
):

    # ==========================================================
    # ENGINEER SECURITY
    # ==========================================================

    if (
        request.user.role != "ENGINEER"
        and not request.user.is_superuser
    ):
        return HttpResponseForbidden(
            "Only Primexa engineers can review delivery risks."
        )

    # ==========================================================
    # GET ALERT
    # ==========================================================

    alert = get_object_or_404(
        DeliveryRiskAlert.objects.select_related(
            "cad_model",
            "vendor",
            "reviewed_by",
        ),
        id=alert_id,
    )

    # ==========================================================
    # POST
    # ==========================================================

    if request.method == "POST":

        decision = (
            request.POST
            .get(
                "decision",
                "",
            )
            .strip()
            .upper()
        )

        remarks = (
            request.POST
            .get(
                "engineer_remarks",
                "",
            )
            .strip()
        )

        # ======================================================
        # ACCEPT REVISED DELIVERY
        # ======================================================

        if decision == "ACCEPT":

            alert.status = "ACCEPTED"

        # ======================================================
        # REQUEST RECOVERY PLAN
        # ======================================================

        elif decision == "RECOVERY":

            alert.status = (
                "RECOVERY_REQUESTED"
            )

        # ======================================================
        # RESOLVE
        # ======================================================

        elif decision == "RESOLVE":

            alert.status = "RESOLVED"

        # ======================================================
        # INVALID DECISION
        # ======================================================

        else:

            return HttpResponseForbidden(
                "Invalid delivery-risk decision."
            )

        # ======================================================
        # ENGINEER REVIEW DATA
        # ======================================================

        alert.engineer_remarks = remarks

        alert.reviewed_by = (
            request.user
        )

        alert.reviewed_at = (
            timezone.now()
        )

        # ======================================================
        # SAVE REVIEW
        # ======================================================

        alert.save()

        # ======================================================
        # RETURN TO ENGINEER DASHBOARD
        # ======================================================

        return redirect(
            "engineer_dashboard"
        )

    # ==========================================================
    # DISPLAY REVIEW PAGE
    # ==========================================================

    return render(
        request,
        "exchange/review_delivery_risk.html",
        {
            "alert": alert,
        },
    )