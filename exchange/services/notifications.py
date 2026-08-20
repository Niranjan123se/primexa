
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from exchange.models import NotificationLog
from users.models import User


# ==========================================================
# CENTRAL PRIMEXA NOTIFICATION ENGINE
# ==========================================================

def send_notification(
    *,
    notification_type,
    recipient,
    subject,
    message,
    cad_model=None,
    template_name=None,
    context=None,
):
    """
    Central Primexa notification engine.

    Responsibilities:
    1. Validate recipient.
    2. Create NotificationLog.
    3. Send plain-text email.
    4. Optionally send HTML email.
    5. Mark notification SENT / FAILED.
    6. Store error information if delivery fails.

    Returns:
        NotificationLog instance
        or None when recipient/email is unavailable.
    """

    if not recipient:
        return None

    recipient_email = getattr(
        recipient,
        "email",
        None,
    )

    if not recipient_email:
        return None

    notification = NotificationLog.objects.create(
        cad_model=cad_model,
        recipient=recipient,
        recipient_email=recipient_email,
        notification_type=notification_type,
        subject=subject,
        message=message,
        status="PENDING",
    )

    try:

        html_message = None

        if template_name:

            email_context = context or {}

            html_message = render_to_string(
                template_name,
                email_context,
            )

        email = EmailMultiAlternatives(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )

        if html_message:

            email.attach_alternative(
                html_message,
                "text/html",
            )

        email.send(
            fail_silently=False,
        )

        notification.status = "SENT"
        notification.sent_at = timezone.now()

        notification.save(
            update_fields=[
                "status",
                "sent_at",
            ],
        )

        return notification

    except Exception as exc:

        notification.status = "FAILED"
        notification.error_message = str(exc)

        notification.save(
            update_fields=[
                "status",
                "error_message",
            ],
        )

        return notification


# ==========================================================
# COMMON HELPERS
# ==========================================================

def _company_name(user):
    """
    Safely return company name where available.
    """

    if not user:
        return "User"

    return (
        getattr(
            user,
            "company_name",
            None,
        )
        or getattr(
            user,
            "username",
            "User",
        )
    )


def _site_url():
    """
    Safely return configured Primexa site URL.

    Removes trailing slash so URLs can be constructed
    consistently.
    """

    return getattr(
        settings,
        "SITE_URL",
        "",
    ).rstrip("/")


def _email_template():
    """
    Central Primexa HTML email template.
    """

    return "emails/base_notification.html"


# ==========================================================
# 1. REQUIREMENT SUBMITTED
#
# OEM
# ↓
# PRIMEXA ENGINEERS
# ==========================================================

def notify_requirement_submitted(cad_model):

    engineers = User.objects.filter(
        role="ENGINEER",
        is_active=True,
    )

    notifications = []

    site_url = _site_url()

    for engineer in engineers:

        notification = send_notification(

            notification_type=(
                "REQUIREMENT_SUBMITTED"
            ),

            recipient=engineer,

            subject=(
                "[Primexa] New Manufacturing "
                f"Requirement - "
                f"{cad_model.tracking_number}"
            ),

            message=(
                "A new manufacturing requirement "
                "has been submitted.\n\n"

                f"Requirement: "
                f"{cad_model.title}\n"

                f"Tracking Number: "
                f"{cad_model.tracking_number}\n"

                f"Quantity: "
                f"{cad_model.batch_quantity}\n\n"

                "The requirement is awaiting "
                "Primexa engineering review."
            ),

            cad_model=cad_model,

            template_name=_email_template(),

            context={

                "subject": (
                    "New Manufacturing Requirement - "
                    f"{cad_model.tracking_number}"
                ),

                "notification_label": (
                    "ACTION REQUIRED"
                ),

                "email_title": (
                    "New Manufacturing Requirement"
                ),

                "email_body": (
                    "A new manufacturing requirement "
                    "has been submitted and is awaiting "
                    "Primexa engineering review.\n\n"

                    "Please review the technical "
                    "information and decide whether "
                    "the requirement can be published "
                    "to verified manufacturing partners."
                ),

                "cad_model": cad_model,

                "action_text": (
                    "Review Requirement"
                ),

                "action_url": (
                    f"{site_url}/exchange/review/"
                    f"{cad_model.id}/"
                ),
            },
        )

        notifications.append(
            notification
        )

    return notifications


# ==========================================================
# 2. REQUIREMENT PUBLISHED
#
# PRIMEXA ENGINEER
# ↓
# VERIFIED VENDORS
# ==========================================================

def notify_requirement_published(cad_model):

    vendors = User.objects.filter(
        role="VENDOR",
        is_active=True,
    )

    notifications = []

    site_url = _site_url()

    for vendor in vendors:

        notification = send_notification(

            notification_type=(
                "REQUIREMENT_PUBLISHED"
            ),

            recipient=vendor,

            subject=(
                "[Primexa Opportunity] "
                f"{cad_model.tracking_number}"
            ),

            message=(
                "A new manufacturing opportunity "
                "has been published on Primexa.\n\n"

                f"Requirement: "
                f"{cad_model.title}\n"

                f"Tracking Number: "
                f"{cad_model.tracking_number}\n"

                f"Quantity: "
                f"{cad_model.batch_quantity}\n\n"

                "Log in to your vendor dashboard "
                "to review the requirement, sign "
                "the NDA and submit your quotation."
            ),

            cad_model=cad_model,

            template_name=_email_template(),

            context={

                "subject": (
                    "New Manufacturing Opportunity - "
                    f"{cad_model.tracking_number}"
                ),

                "notification_label": (
                    "NEW OPPORTUNITY"
                ),

                "email_title": (
                    "New Manufacturing Opportunity"
                ),

                "email_body": (
                    "A new manufacturing requirement "
                    "has been published on the Primexa "
                    "Exchange.\n\n"

                    "Review the technical requirement "
                    "and submit your competitive "
                    "commercial proposal."
                ),

                "cad_model": cad_model,

                "action_text": (
                    "View Opportunity"
                ),

                "action_url": (
                    f"{site_url}/exchange/vendor/"
                ),
            },
        )

        notifications.append(
            notification
        )

    return notifications


# ==========================================================
# 3. BID SUBMITTED
#
# VENDOR
# ↓
# PRIMEXA ENGINEERS
# ==========================================================

def notify_bid_submitted(
    cad_model,
    bid,
):

    engineers = User.objects.filter(
        role="ENGINEER",
        is_active=True,
    )

    notifications = []

    site_url = _site_url()

    vendor_name = _company_name(
        bid.vendor
    )

    for engineer in engineers:

        notification = send_notification(

            notification_type=(
                "BID_SUBMITTED"
            ),

            recipient=engineer,

            subject=(
                "[Primexa] New Vendor Bid - "
                f"{cad_model.tracking_number}"
            ),

            message=(
                "A vendor has submitted "
                "a new commercial bid.\n\n"

                f"Requirement: "
                f"{cad_model.title}\n"

                f"Tracking Number: "
                f"{cad_model.tracking_number}\n"

                f"Vendor: "
                f"{vendor_name}\n"

                f"Bid Amount: INR "
                f"{bid.offered_price}\n"

                f"Delivery: "
                f"{bid.delivery_days} Days\n\n"

                "Please log in to the Engineering "
                "Control Center to evaluate the bid."
            ),

            cad_model=cad_model,

            template_name=_email_template(),

            context={

                "subject": (
                    "New Vendor Bid - "
                    f"{cad_model.tracking_number}"
                ),

                "notification_label": (
                    "ACTION REQUIRED"
                ),

                "email_title": (
                    "New Vendor Bid Received"
                ),

                "email_body": (
                    "A vendor has submitted a "
                    "commercial bid for this "
                    "manufacturing requirement.\n\n"

                    f"Vendor: {vendor_name}\n"

                    f"Bid Amount: INR "
                    f"{bid.offered_price}\n"

                    f"Delivery: "
                    f"{bid.delivery_days} Days\n\n"

                    "Review the bid and compare "
                    "it with other vendor proposals."
                ),

                "cad_model": cad_model,

                "action_text": (
                    "Manage Vendor Bids"
                ),

                "action_url": (
                    f"{site_url}/exchange/manage-bids/"
                    f"{cad_model.id}/"
                ),
            },
        )

        notifications.append(
            notification
        )

    return notifications


# ==========================================================
# 4. COMMERCIAL PROPOSAL SENT TO OEM
#
# VENDOR BID
# ↓
# PRIMEXA MARGIN
# ↓
# OEM APPROVAL REQUIRED
# ==========================================================

def notify_commercial_proposal(
    cad_model,
    winning_bid,
    margin_percentage,
    vendor_cost,
    primexa_quote,
):

    oem = cad_model.uploaded_by

    site_url = _site_url()

    if not oem:
        return None

    return send_notification(

        notification_type=(
            "COMMERCIAL_PROPOSAL_SENT"
        ),

        recipient=oem,

        subject=(
            "[Primexa Approval Required] "
            "Commercial Proposal - "
            f"{cad_model.tracking_number}"
        ),

        message=(
            "Primexa has completed the vendor "
            "commercial evaluation.\n\n"

            f"Requirement: "
            f"{cad_model.title}\n"

            f"Tracking Number: "
            f"{cad_model.tracking_number}\n\n"

            f"Final Primexa Quote: "
            f"INR {primexa_quote:.2f}\n"

            f"Estimated Delivery: "
            f"{winning_bid.delivery_days} Days\n\n"

            "Please log in to the OEM dashboard "
            "to approve or reject the commercial "
            "proposal.\n\n"

            "The manufacturing vendor will NOT "
            "receive the final award until your "
            "approval is received."
        ),

        cad_model=cad_model,

        template_name=_email_template(),

        context={

            "subject": (
                "Commercial Proposal Approval Required - "
                f"{cad_model.tracking_number}"
            ),

            "notification_label": (
                "OEM APPROVAL REQUIRED"
            ),

            "email_title": (
                "Commercial Proposal Ready"
            ),

            "email_body": (
                "Primexa has completed the vendor "
                "evaluation and prepared the final "
                "commercial proposal for your approval.\n\n"

                f"Final Primexa Quote: "
                f"INR {primexa_quote:.2f}\n\n"

                f"Estimated Delivery: "
                f"{winning_bid.delivery_days} Days\n\n"

                "Please review the proposal and "
                "approve or reject it from your "
                "OEM dashboard."
            ),

            "cad_model": cad_model,

            "action_text": (
                "Review & Approve Quote"
            ),

            "action_url": (
                f"{site_url}/exchange/oem-approve/"
                f"{cad_model.id}/"
            ),

            "commercial_proposal": True,

            "vendor_cost": vendor_cost,

            "margin_percentage": (
                margin_percentage
            ),

            "primexa_quote": (
                primexa_quote
            ),

            "delivery_days": (
                winning_bid.delivery_days
            ),
        },
    )


# ==========================================================
# 5. OEM APPROVED COMMERCIAL PROPOSAL
#
# OEM
# ↓
# PRIMEXA ENGINEERS
# ==========================================================

def notify_oem_approved(cad_model):

    engineers = User.objects.filter(
        role="ENGINEER",
        is_active=True,
    )

    notifications = []

    site_url = _site_url()

    for engineer in engineers:

        quote = (
            cad_model.final_primexa_quote
            or 0
        )

        notification = send_notification(

            notification_type=(
                "OEM_COMMERCIAL_APPROVED"
            ),

            recipient=engineer,

            subject=(
                "[Primexa] OEM Approved - "
                "Final Vendor Award Required - "
                f"{cad_model.tracking_number}"
            ),

            message=(
                "The OEM has approved the "
                "commercial proposal.\n\n"

                f"Requirement: "
                f"{cad_model.title}\n"

                f"Tracking Number: "
                f"{cad_model.tracking_number}\n"

                f"Approved Quote: INR "
                f"{quote:.2f}\n\n"

                "The requirement is now ready "
                "for final vendor award."
            ),

            cad_model=cad_model,

            template_name=_email_template(),

            context={

                "subject": (
                    "OEM Approved - Final Award Required - "
                    f"{cad_model.tracking_number}"
                ),

                "notification_label": (
                    "OEM APPROVED"
                ),

                "email_title": (
                    "Commercial Proposal Approved"
                ),

                "email_body": (
                    "The OEM has approved the "
                    "Primexa commercial proposal.\n\n"

                    f"Approved Quote: INR "
                    f"{quote:.2f}\n\n"

                    "The requirement is now ready "
                    "for final vendor award."
                ),

                "cad_model": cad_model,

                "action_text": (
                    "Issue Final Vendor Award"
                ),

                "action_url": (
                    f"{site_url}/exchange/final-award/"
                    f"{cad_model.id}/"
                ),
            },
        )

        notifications.append(
            notification
        )

    return notifications


# ==========================================================
# 6. OEM REJECTED COMMERCIAL PROPOSAL
#
# OEM
# ↓
# PRIMEXA ENGINEERS
#
# NO VENDOR AWARD ALLOWED
# ==========================================================

def notify_oem_rejected(
    cad_model,
    remarks="",
):

    engineers = User.objects.filter(
        role="ENGINEER",
        is_active=True,
    )

    notifications = []

    site_url = _site_url()

    for engineer in engineers:

        notification = send_notification(

            notification_type=(
                "OEM_COMMERCIAL_REJECTED"
            ),

            recipient=engineer,

            subject=(
                "[Primexa] Commercial Proposal Rejected - "
                f"{cad_model.tracking_number}"
            ),

            message=(
                "The OEM has rejected the "
                "commercial proposal.\n\n"

                f"Requirement: "
                f"{cad_model.title}\n"

                f"Tracking Number: "
                f"{cad_model.tracking_number}\n\n"

                f"OEM Remarks: "
                f"{remarks or 'No remarks provided.'}\n\n"

                "Final vendor award is blocked. "
                "Primexa action is required."
            ),

            cad_model=cad_model,

            template_name=_email_template(),

            context={

                "subject": (
                    "Commercial Proposal Rejected - "
                    f"{cad_model.tracking_number}"
                ),

                "notification_label": (
                    "ACTION REQUIRED"
                ),

                "email_title": (
                    "OEM Rejected Commercial Proposal"
                ),

                "email_body": (
                    "The OEM has rejected the "
                    "commercial proposal.\n\n"

                    f"Remarks: "
                    f"{remarks or 'No remarks provided.'}\n\n"

                    "Review the requirement and "
                    "determine the next commercial action."
                ),

                "cad_model": cad_model,

                "action_text": (
                    "Review Requirement"
                ),

                "action_url": (
                    f"{site_url}/exchange/manage-bids/"
                    f"{cad_model.id}/"
                ),

                "remarks": remarks,
            },
        )

        notifications.append(
            notification
        )

    return notifications


# ==========================================================
# 7. FINAL VENDOR AWARD
#
# PRIMEXA
# ↓
# SELECTED VENDOR
# ==========================================================

def notify_vendor_final_award(cad_model):

    vendor = cad_model.selected_vendor

    if not vendor:
        return None

    site_url = _site_url()

    vendor_cost = (
        cad_model.accepted_vendor_cost
        or 0
    )

    return send_notification(

        notification_type=(
            "FINAL_VENDOR_AWARD"
        ),

        recipient=vendor,

        subject=(
            "[Primexa Final Award] "
            f"{cad_model.tracking_number}"
        ),

        message=(
            "Congratulations.\n\n"

            "Primexa has officially awarded "
            "the manufacturing requirement "
            "to your organization.\n\n"

            f"Requirement: "
            f"{cad_model.title}\n"

            f"Tracking Number: "
            f"{cad_model.tracking_number}\n"

            f"Quantity: "
            f"{cad_model.batch_quantity}\n\n"

            f"Approved Manufacturing Cost: "
            f"INR {vendor_cost:.2f}\n\n"

            "The OEM has approved the commercial "
            "proposal and the final manufacturing "
            "award is now active.\n\n"

            "Please proceed with the next "
            "onboarding and production instructions."
        ),

        cad_model=cad_model,

        template_name=_email_template(),

        context={

            "subject": (
                "Final Manufacturing Award - "
                f"{cad_model.tracking_number}"
            ),

            "notification_label": (
                "FINAL AWARD"
            ),

            "email_title": (
                "Manufacturing Requirement Awarded"
            ),

            "email_body": (
                "Primexa has officially awarded "
                "this manufacturing requirement "
                "to your organization.\n\n"

                f"Requirement: "
                f"{cad_model.title}\n"

                f"Quantity: "
                f"{cad_model.batch_quantity}\n\n"

                "Please proceed with the next "
                "manufacturing and onboarding steps."
            ),

            "cad_model": cad_model,

            "action_text": (
                "View Award"
            ),

            "action_url": (
                f"{site_url}/exchange/vendor/"
            ),
        },
    )


# ==========================================================
# 8. FINAL AWARD CONFIRMATION TO OEM
#
# PRIMEXA
# ↓
# OEM
# ==========================================================

def notify_oem_final_award(cad_model):

    oem = cad_model.uploaded_by

    if not oem:
        return None

    site_url = _site_url()

    quote = (
        cad_model.final_primexa_quote
        or 0
    )

    return send_notification(

        notification_type=(
            "FINAL_AWARD_CONFIRMATION"
        ),

        recipient=oem,

        subject=(
            "[Primexa Award Confirmation] "
            f"{cad_model.tracking_number}"
        ),

        message=(
            "Your approved manufacturing "
            "requirement has now been officially "
            "awarded to the selected manufacturing "
            "partner.\n\n"

            f"Requirement: "
            f"{cad_model.title}\n"

            f"Tracking Number: "
            f"{cad_model.tracking_number}\n\n"

            f"Approved Primexa Quote: "
            f"INR {quote:.2f}\n\n"

            "Primexa will coordinate the next "
            "stages of manufacturing execution, "
            "quality control and delivery."
        ),

        cad_model=cad_model,

        template_name=_email_template(),

        context={

            "subject": (
                "Final Manufacturing Award Confirmation - "
                f"{cad_model.tracking_number}"
            ),

            "notification_label": (
                "AWARD CONFIRMED"
            ),

            "email_title": (
                "Manufacturing Award Confirmed"
            ),

            "email_body": (
                "Your approved manufacturing "
                "requirement has been officially "
                "awarded to the selected manufacturing "
                "partner.\n\n"

                f"Approved Primexa Quote: "
                f"INR {quote:.2f}\n\n"

                "Primexa will coordinate the next "
                "stages of manufacturing execution."
            ),

            "cad_model": cad_model,

            "action_text": (
                "View Requirement"
            ),

            "action_url": (
                f"{site_url}/exchange/oem/"
            ),
        },
    )
# ==========================================================
# DELIVERY RISK ALERT
#
# VENDOR
# ↓
# PRIMEXA ENGINEERS
# ==========================================================

def notify_delivery_risk(alert):

    engineers = User.objects.filter(
        role="ENGINEER",
        is_active=True,
    )

    site_url = _site_url()

    notifications = []

    for engineer in engineers:

        subject = (
            "[Primexa URGENT] Delivery Risk - "
            f"{alert.cad_model.tracking_number}"
        )

        message = (
            "A vendor has reported a delivery risk.\n\n"

            f"Requirement: "
            f"{alert.cad_model.title}\n"

            f"Tracking Number: "
            f"{alert.cad_model.tracking_number}\n\n"

            f"Vendor: "
            f"{_company_name(alert.vendor)}\n\n"

            f"Original Delivery: "
            f"{alert.original_delivery_date}\n"

            f"Revised Delivery: "
            f"{alert.revised_delivery_date}\n\n"

            f"Reason: "
            f"{alert.get_reason_display()}\n"

            f"Production Status: "
            f"{alert.get_production_status_display()}\n\n"

            f"Quantity Completed: "
            f"{alert.quantity_completed}\n"

            f"Quantity Remaining: "
            f"{alert.quantity_remaining}\n\n"

            "Vendor Remarks:\n"
            f"{alert.issue_description}\n\n"

            "Please review the delivery risk immediately."
        )

        notification = send_notification(
            notification_type="DELIVERY_RISK",
            recipient=engineer,
            subject=subject,
            message=message,
            cad_model=alert.cad_model,
            template_name=_email_template(),
            context={
                "subject": subject,
                "notification_label": "URGENT DELIVERY RISK",
                "email_title": (
                    "Vendor Delivery Risk Reported"
                ),
                "email_body": (
                    "A manufacturing vendor has "
                    "reported that the current delivery "
                    "commitment is at risk."
                ),
                "cad_model": alert.cad_model,
                "action_text": (
                    "Review Delivery Risk"
                ),
                "action_url": (
                    f"{site_url}/exchange/delivery-risk/"
                    f"review/{alert.id}/"
                ),
            },
        )

        notifications.append(
            notification
        )

    return notifications
# ==========================================================
# FAI REJECTED
#
# PRIMEXA ENGINEER
#        ↓
# VENDOR
#
# Vendor must correct FAI and resubmit.
# ==========================================================


def notify_fai_rejected(
    fai_record,
    remarks="",
):

    vendor = fai_record.vendor

    if not vendor:
        return None

    cad_model = fai_record.cad_model

    site_url = _site_url()

    rejection_reason = (
        remarks.strip()
        if remarks
        else "No specific rejection remarks were provided."
    )

    notification = send_notification(

        notification_type=(
            "FAI_REJECTED"
        ),

        recipient=vendor,

        subject=(
            "[Primexa] FAI Rejected - "
            f"{cad_model.tracking_number}"
        ),

        message=(
            "Your First Article Inspection submission "
            "has been rejected by Primexa Engineering.\n\n"

            f"Requirement: "
            f"{cad_model.title}\n"

            f"Tracking Number: "
            f"{cad_model.tracking_number}\n\n"

            "Engineering Remarks:\n"
            f"{rejection_reason}\n\n"

            "Please review the engineering remarks, "
            "correct the required documentation or "
            "inspection information and resubmit the FAI."
        ),

        cad_model=cad_model,

        template_name=_email_template(),

        context={

            "subject": (
                "FAI Rejected - "
                f"{cad_model.tracking_number}"
            ),

            "notification_label": (
                "FAI REJECTED"
            ),

            "email_title": (
                "First Article Inspection Rejected"
            ),

            "email_body": (
                "Your First Article Inspection "
                "submission has been rejected by "
                "Primexa Engineering.\n\n"

                "Please review the engineering "
                "remarks and correct the submission "
                "before resubmitting."
            ),

            "cad_model": cad_model,

            "action_text": (
                "Review FAI Requirements"
            ),

            "action_url": (
                f"{site_url}/exchange/vendor/"
            ),
        },
    )

    return notification