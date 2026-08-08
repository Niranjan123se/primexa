import uuid
import hashlib

from django.db import models
from users.models import User

def generate_tracking_number():
    return f"FX-360-{str(uuid.uuid4()).upper()[:6]}"


class CADModel(models.Model):

    STATUS_CHOICES = [
        ("PENDING", "Pending Primexa Review"),
        ("PUBLISHED", "Published to Vendors"),
        ("BID_PLACED", "Bids Placed by Vendors"),
        ("REVIEWED_SHORTLISTED", "Primexa Engineer Reviewed & Shortlisted"),
        ("FAI_PENDING", "First Article Inspection (FAI) Pending Approval"),
        ("FAI_APPROVED", "FAI Approved - Ready for Production"),
        ("OEM_APPROVAL_PENDING", "Commercial Quote Sent to OEM - Approval Pending"),
        ("OEM_APPROVED", "OEM Approved - Ready for Final Award"),
        ("OEM_REJECTED", "OEM Rejected Commercial Quote"),
        ("REJECTED", "Requirement Rejected"),
        ("VENDOR_AWARDED", "Vendor Awarded & Subcontracted"),
        ("FINAL_VENDOR_ONBOARDED", "Final Vendor Onboarded & Order Placed"),
        ("COMPLETED", "Order Completed"),
    ]

    JOB_TYPE_CHOICES = [
        ("SINGLE", "Single Component Job"),
        ("ASSEMBLY", "Assembly (Multiple Drawings / ZIP Package)"),
    ]

    WORK_NATURE_CHOICES = [
        ("NEW", "New Development (Prototype & FAI)"),
        ("PRODUCTION", "Regular Production / Batch Run"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    tracking_number = models.CharField(
        max_length=50,
        unique=True,
        default=generate_tracking_number,
        editable=False,
    )

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="uploaded_cad_models",
    )

    title = models.CharField(
        max_length=255,
        default="New Requirement",
    )

    description = models.TextField(
        blank=True,
        null=True,
    )

    file = models.FileField(
        upload_to="secure_cad_models/",
        blank=True,
        null=True,
    )

    job_category = models.CharField(
        max_length=20,
        choices=JOB_TYPE_CHOICES,
        default="SINGLE",
    )

    work_nature = models.CharField(
        max_length=20,
        choices=WORK_NATURE_CHOICES,
        default="PRODUCTION",
    )

    batch_quantity = models.PositiveIntegerField(
        default=1,
    )

    target_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
    )

    vendor_qualifications_required = models.TextField(
        blank=True,
        null=True,
    )

    expected_delivery_date = models.DateField(
        blank=True,
        null=True,
    )

    fai_remarks = models.TextField(
        blank=True,
        null=True,
    )

    accepted_vendor_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    platform_margin_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=15.00,
    )

    final_primexa_quote = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    selected_vendor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subcontracted_jobs",
    )

    # OEM COMMERCIAL APPROVAL
    oem_approval_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    oem_approval_remarks = models.TextField(
        blank=True,
        null=True,
    )

    oem_approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_oem_quotes",
    )

    status = models.CharField(
        max_length=40,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f"{self.tracking_number} - {self.title}"


class WorkloadTransfer(models.Model):

    cad_model = models.ForeignKey(
        CADModel,
        on_delete=models.CASCADE,
        related_name="workload_transfers",
    )

    sub_vendor = models.ForeignKey(
        User,
        related_name="incoming_work",
        on_delete=models.CASCADE,
    )

    nda_signed_by_sub = models.BooleanField(
        default=False,
    )

    agreed_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
    )

    signature_hash = models.CharField(
        max_length=64,
        blank=True,
        null=True,
    )

    def save(self, *args, **kwargs):
        if self.nda_signed_by_sub and not self.signature_hash:
            raw_data = (
                f"{self.cad_model.id}-"
                f"{self.sub_vendor.id}-"
                f"{self.agreed_at}-"
                f"{self.ip_address}"
            )
            self.signature_hash = hashlib.sha256(
                raw_data.encode("utf-8")
            ).hexdigest()

        super().save(*args, **kwargs)

    def __str__(self):
        hash_display = (
            self.signature_hash[:10]
            if self.signature_hash
            else "PENDING"
        )
        return (
            f"NDA Proof: "
            f"{self.cad_model.tracking_number} - "
            f"{self.sub_vendor.username} "
            f"[{hash_display}...]"
        )


class Bid(models.Model):

    cad_model = models.ForeignKey(
        CADModel,
        on_delete=models.CASCADE,
        related_name="bids",
    )

    vendor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="bids_placed",
    )

    offered_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    delivery_days = models.PositiveIntegerField()

    proposal_notes = models.TextField(
        blank=True,
        null=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return (
            f"Bid by {self.vendor.username} "
            f"for {self.cad_model.tracking_number} "
            f"- INR {self.offered_price}"
        )