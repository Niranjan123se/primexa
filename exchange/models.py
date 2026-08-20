import hashlib
import uuid

from django.db import models

from users.models import User, VendorProfile
from django.conf import settings


# ==========================================================
# TRACKING NUMBER
# ==========================================================

def generate_tracking_number():
    """
    Generate a unique Primexa manufacturing requirement number.

    Example:
    PX-360-A1B2C3
    """
    return f"PX-360-{str(uuid.uuid4()).upper()[:6]}"


# ==========================================================
# CAD / MANUFACTURING REQUIREMENT
# ==========================================================

class CADModel(models.Model):

    # ======================================================
    # REQUIREMENT STATUS
    # ======================================================

    STATUS_CHOICES = [

        ("PENDING", "Pending Primexa Review"),

        ("PUBLISHED", "Published to Vendors"),

        ("BID_PLACED", "Bids Placed by Vendors"),

        (
            "REVIEWED_SHORTLISTED",
            "Primexa Engineer Reviewed & Shortlisted",
        ),

        (
            "FAI_PENDING",
            "First Article Inspection (FAI) Pending Approval",
        ),

        (
            "FAI_APPROVED",
            "FAI Approved - Ready for Production",
        ),
        (
            "FAI_REJECTED",
            "FAI Rejected",
        ),

        (
            "OEM_APPROVAL_PENDING",
            "Commercial Quote Sent to OEM - Approval Pending",
        ),

        (
            "OEM_APPROVED",
            "OEM Approved - Ready for Final Award",
        ),

        (
            "OEM_REJECTED",
            "OEM Rejected Commercial Quote",
        ),

        (
            "REJECTED",
            "Requirement Rejected",
        ),

        (
            "VENDOR_AWARDED",
            "Vendor Awarded & Subcontracted",
        ),

        (
            "FINAL_VENDOR_ONBOARDED",
            "Final Vendor Onboarded & Order Placed",
        ),

        (
            "COMPLETED",
            "Order Completed",
        ),
    ]

    # ======================================================
    # JOB TYPE
    # ======================================================

    JOB_TYPE_CHOICES = [

        (
            "SINGLE",
            "Single Component Job",
        ),

        (
            "ASSEMBLY",
            "Assembly (Multiple Drawings / ZIP Package)",
        ),
    ]

    # ======================================================
    # WORK NATURE
    # ======================================================

    WORK_NATURE_CHOICES = [

        (
            "NEW",
            "New Development (Prototype & FAI)",
        ),

        (
            "PRODUCTION",
            "Regular Production / Batch Run",
        ),
    ]

    # ======================================================
    # PRIMARY IDENTIFICATION
    # ======================================================

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

    # ======================================================
    # OEM / REQUIREMENT OWNER
    # ======================================================

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

    # ======================================================
    # CAD / TECHNICAL FILE
    # ======================================================

    file = models.FileField(
        upload_to="secure_cad_models/",
        blank=True,
        null=True,
    )

    # ======================================================
    # REQUIREMENT CLASSIFICATION
    # ======================================================

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

    # ======================================================
    # QUANTITY / COMMERCIAL REQUIREMENT
    # ======================================================

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
    # ======================================================
    # VENDOR DELIVERY COMMITMENT
    # ======================================================

    vendor_committed_delivery_date = models.DateField(
        blank=True,
        null=True,
        help_text="Delivery date committed by the awarded vendor.",
    )

    vendor_awarded_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Date and time when Primexa issued the final vendor award.",
    )

    # ======================================================
    # ENGINEERING / FAI
    # ======================================================

    fai_remarks = models.TextField(
        blank=True,
        null=True,
    )

    # ======================================================
    # COMMERCIAL CONTROL
    # ======================================================

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

    # ======================================================
    # SELECTED VENDOR
    #
    # IMPORTANT:
    # This field means "commercially selected vendor".
    # It does NOT mean final award until status changes
    # to VENDOR_AWARDED.
    # ======================================================

    selected_vendor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subcontracted_jobs",
    )

    # ======================================================
    # OEM COMMERCIAL APPROVAL
    # ======================================================

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

    # ======================================================
    # WORKFLOW STATUS
    # ======================================================

    status = models.CharField(
        max_length=40,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    # ======================================================
    # TIMESTAMPS
    # ======================================================

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
    )

    # ======================================================
    # STRING REPRESENTATION
    # ======================================================

    def __str__(self):
        return (
            f"{self.tracking_number} - "
            f"{self.title}"
        )


# ==========================================================
# WORKLOAD TRANSFER / NDA
# ==========================================================

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

    # ======================================================
    # NDA
    # ======================================================

    nda_signed_by_sub = models.BooleanField(
        default=False,
    )

    agreed_at = models.DateTimeField(
        blank=True,
        null=True,
    )

    # ======================================================
    # SECURITY / AUDIT
    # ======================================================

    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
    )

    signature_hash = models.CharField(
        max_length=64,
        blank=True,
        null=True,
    )

    # ======================================================
    # HASH GENERATION
    # ======================================================

    def save(self, *args, **kwargs):

        if (
            self.nda_signed_by_sub
            and not self.signature_hash
        ):

            raw_data = (
                f"{self.cad_model.id}-"
                f"{self.sub_vendor.id}-"
                f"{self.agreed_at}-"
                f"{self.ip_address}"
            )

            self.signature_hash = hashlib.sha256(
                raw_data.encode("utf-8")
            ).hexdigest()

        super().save(
            *args,
            **kwargs
        )

    # ======================================================
    # STRING REPRESENTATION
    # ======================================================

    def __str__(self):

        hash_display = (
            self.signature_hash[:10]
            if self.signature_hash
            else "PENDING"
        )

        return (
            "NDA Proof: "
            f"{self.cad_model.tracking_number} - "
            f"{self.sub_vendor.username} "
            f"[{hash_display}...]"
        )


# ==========================================================
# VENDOR BID
# ==========================================================

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

    # ======================================================
    # STRING REPRESENTATION
    # ======================================================

    def __str__(self):

        return (
            f"Bid by "
            f"{self.vendor.username} "
            f"for "
            f"{self.cad_model.tracking_number} "
            f"- INR "
            f"{self.offered_price}"
        )


# ==========================================================
# NOTIFICATION LOG
# ==========================================================

class NotificationLog(models.Model):

    # ======================================================
    # NOTIFICATION TYPES
    # ======================================================

    NOTIFICATION_TYPES = [

        (
            "REQUIREMENT_SUBMITTED",
            "Requirement Submitted",
        ),

        (
            "REQUIREMENT_PUBLISHED",
            "Requirement Published",
        ),

        (
            "NDA_SIGNED",
            "NDA Signed",
        ),

        (
            "BID_SUBMITTED",
            "Bid Submitted",
        ),

        (
            "BID_SHORTLISTED",
            "Bid Shortlisted",
        ),

        (
            "COMMERCIAL_PREPARED",
            "Commercial Proposal Prepared",
        ),

        (
            "COMMERCIAL_PROPOSAL_SENT",
            "Commercial Proposal Sent to OEM",
        ),

        (
            "OEM_APPROVAL_PENDING",
            "OEM Approval Required",
        ),

        (
            "OEM_REVISION_REQUESTED",
            "OEM Revision Requested",
        ),

        (
            "OEM_APPROVED",
            "OEM Approved",
        ),

        (
            "OEM_COMMERCIAL_APPROVED",
            "OEM Commercial Proposal Approved",
        ),

        (
            "OEM_REJECTED",
            "OEM Rejected",
        ),

        (
            "OEM_COMMERCIAL_REJECTED",
            "OEM Commercial Proposal Rejected",
        ),

        (
            "FINAL_VENDOR_AWARD",
            "Final Vendor Award",
        ),

        (
            "FINAL_AWARD_CONFIRMATION",
            "Final Award Confirmation",
        ),

        (
            "VENDOR_ACCEPTED",
            "Vendor Accepted Award",
        ),

        (
            "FAI_REQUIRED",
            "FAI Required",
        ),

        (
            "FAI_SUBMITTED",
            "FAI Submitted",
        ),

        (
            "FAI_APPROVED",
            "FAI Approved",
        ),

        (
            "PRODUCTION_STARTED",
            "Production Started",
        ),

        (
            "PRODUCTION_COMPLETED",
            "Production Completed",
        ),

        (
            "DISPATCHED",
            "Order Dispatched",
        ),

        (
            "DELIVERED",
            "Order Delivered",
        ),

        (
            "ORDER_COMPLETED",
            "Order Completed",
        ),

        (
            "REMINDER",
            "Reminder",
        ),
        (
            "DELIVERY_RISK",
            "Delivery Risk Alert",
        ),

        (
            "SYSTEM_ALERT",
            "System Alert",
        ),
        
    ]

    # ======================================================
    # NOTIFICATION STATUS
    # ======================================================

    STATUS_CHOICES = [

        (
            "PENDING",
            "Pending",
        ),

        (
            "SENT",
            "Sent",
        ),

        (
            "FAILED",
            "Failed",
        ),
    ]

    # ======================================================
    # RELATED REQUIREMENT
    # ======================================================

    cad_model = models.ForeignKey(
        CADModel,
        on_delete=models.CASCADE,
        related_name="notification_logs",
        null=True,
        blank=True,
    )

    # ======================================================
    # RECIPIENT
    # ======================================================

    recipient = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="received_notifications",
    )

    recipient_email = models.EmailField()

    # ======================================================
    # NOTIFICATION DETAILS
    # ======================================================

    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES,
    )

    subject = models.CharField(
        max_length=255,
    )

    message = models.TextField()

    # ======================================================
    # DELIVERY STATUS
    # ======================================================

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    error_message = models.TextField(
        blank=True,
        null=True,
    )

    sent_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    # ======================================================
    # STRING REPRESENTATION
    # ======================================================

    def __str__(self):

        return (
            f"{self.notification_type} - "
            f"{self.recipient_email} - "
            f"{self.status}"
        )
# ==========================================================

# FAI — FIRST ARTICLE INSPECTION

# ==========================================================

class FAIRecord(models.Model):


    STATUS_CHOICES = [
        ("PENDING", "FAI Pending"),
        ("SUBMITTED", "FAI Submitted"),
        ("APPROVED", "FAI Approved"),
        ("REJECTED", "FAI Rejected"),
    ]

    cad_model = models.OneToOneField(
        CADModel,
        on_delete=models.CASCADE,
        related_name="fai_record",
    )


    vendor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fai_records",
    )

    # ======================================================
    # FAI STATUS
    # ======================================================

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
    )

    # ======================================================
    # VENDOR SUBMISSION
    # ======================================================

    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    inspection_report = models.FileField(
        upload_to="fai/inspection_reports/",
        null=True,
        blank=True,
    )

    inspection_notes = models.TextField(
        blank=True,
        null=True,
    )

    dimensional_report = models.FileField(
        upload_to="fai/dimensional_reports/",
        null=True,
        blank=True,
    )

    material_certificate = models.FileField(
        upload_to="fai/material_certificates/",
        null=True,
        blank=True,
    )

    other_documents = models.FileField(
        upload_to="fai/other_documents/",
        null=True,
        blank=True,
    )

    # ======================================================
    # PRIMEXA ENGINEER REVIEW
    # ======================================================

    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_fai_records",
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    engineer_remarks = models.TextField(
        blank=True,
        null=True,
    )

    # ======================================================
    # AUDIT
    # ======================================================

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    # ======================================================
    # STRING REPRESENTATION
    # ======================================================

    def __str__(self):
        return (
            f"FAI - "
            f"{self.cad_model.tracking_number} - "
            f"{self.status}"
        )
# ==========================================================
# DELIVERY RISK ALERT
# ==========================================================

class DeliveryRiskAlert(models.Model):

    REASON_CHOICES = [
        ("MACHINE_BREAKDOWN", "Machine Breakdown"),
        ("RAW_MATERIAL_DELAY", "Raw Material Delay"),
        ("POWER_UTILITY", "Power / Utility Issue"),
        ("MANPOWER", "Manpower Issue"),
        ("QUALITY_REWORK", "Quality / Rework Issue"),
        ("CAPACITY", "Capacity Issue"),
        ("TRANSPORT", "Transport Issue"),
        ("EXTERNAL_DEPENDENCY", "Customer / External Dependency"),
        ("OTHER", "Other"),
    ]

    PRODUCTION_STATUS_CHOICES = [
        ("NOT_STARTED", "Not Started"),
        ("IN_PRODUCTION", "In Production"),
        ("PARTIALLY_COMPLETED", "Partially Completed"),
        (
            "COMPLETED_AWAITING_DISPATCH",
            "Completed - Awaiting Dispatch",
        ),
    ]

    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("UNDER_REVIEW", "Under Engineer Review"),
        ("RECOVERY_REQUESTED", "Recovery Plan Requested"),
        ("ACCEPTED", "Revised Delivery Accepted"),
        ("RESOLVED", "Resolved"),
        ("REALLOCATED", "Work Reallocated"),
    ]

    # ------------------------------------------------------
    # REQUIREMENT
    # ------------------------------------------------------

    cad_model = models.ForeignKey(
        CADModel,
        on_delete=models.CASCADE,
        related_name="delivery_risk_alerts",
    )

    # ------------------------------------------------------
    # REPORTING VENDOR
    # ------------------------------------------------------

    vendor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="delivery_risk_alerts",
    )

    # ------------------------------------------------------
    # DELIVERY DATES
    # ------------------------------------------------------

    original_delivery_date = models.DateField()

    revised_delivery_date = models.DateField()

    # ------------------------------------------------------
    # RISK INFORMATION
    # ------------------------------------------------------

    reason = models.CharField(
        max_length=40,
        choices=REASON_CHOICES,
    )

    production_status = models.CharField(
        max_length=40,
        choices=PRODUCTION_STATUS_CHOICES,
    )

    quantity_completed = models.PositiveIntegerField(
        default=0,
    )

    quantity_remaining = models.PositiveIntegerField(
        default=0,
    )

    issue_description = models.TextField()

    supporting_document = models.FileField(
        upload_to="delivery_risk/",
        blank=True,
        null=True,
    )

    # ------------------------------------------------------
    # WORKFLOW
    # ------------------------------------------------------

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="OPEN",
    )

    # ------------------------------------------------------
    # ENGINEER REVIEW
    # ------------------------------------------------------

    engineer_remarks = models.TextField(
        blank=True,
        null=True,
    )

    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_delivery_risks",
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    # ------------------------------------------------------
    # TIMESTAMPS
    # ------------------------------------------------------

    reported_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):
        return (
            f"Delivery Risk - "
            f"{self.cad_model.tracking_number} - "
            f"{self.vendor.username}"
        )
# ==============================================================
# MANUFACTURING PROCESS
# ==============================================================


class ManufacturingProcess(models.Model):

    PROCESS_CHOICES = [
        ("TURNING", "Turning"),
        ("MILLING", "Milling"),
        ("VMC", "VMC"),
        ("HMC", "HMC"),
        ("CNC", "CNC"),
        ("GRINDING", "Grinding"),
        ("EDM", "EDM"),
        ("WIRE_CUT", "Wire Cut"),
        ("FABRICATION", "Fabrication"),
        ("WELDING", "Welding"),
        ("HEAT_TREATMENT", "Heat Treatment"),
        ("HARDENING", "Hardening"),
        ("ANNEALING", "Annealing"),
        ("COATING", "Coating"),
        ("ANODIZING", "Anodizing"),
        ("PLATING", "Plating"),
        ("PAINTING", "Painting"),
        ("SHOT_BLASTING", "Shot Blasting"),
        ("LASER_CUTTING", "Laser Cutting"),
        ("INSPECTION", "Inspection"),
        ("ASSEMBLY", "Assembly"),
        ("PACKAGING", "Packaging"),
        ("OTHER", "Other"),
    ]

    cad_model = models.ForeignKey(
        CADModel,
        on_delete=models.CASCADE,
        related_name="manufacturing_processes",
    )

    process_type = models.CharField(
        max_length=50,
        choices=PROCESS_CHOICES,
    )

    sequence = models.PositiveIntegerField(
        default=1,
    )

    quantity = models.PositiveIntegerField(
        default=1,
    )

    description = models.TextField(
        blank=True,
    )

    required_machine = models.CharField(
        max_length=150,
        blank=True,
    )

    tolerance_requirement = models.CharField(
        max_length=150,
        blank=True,
    )

    is_mandatory = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:

        ordering = [
            "sequence",
        ]

    def __str__(self):

        return (
            f"{self.cad_model.title} - "
            f"{self.get_process_type_display()} "
            f"({self.sequence})"
        )
# ==============================================================
# MACHINE AVAILABILITY
# ==============================================================





# ==========================================================
# VENDOR SERVICE CATEGORY
# ==========================================================


class VendorServiceCategory(models.Model):

    CATEGORY_CHOICES = [
        (
            "MATERIAL",
            "Material Supplier",
        ),

        (
            "MANUFACTURING",
            "Manufacturing / Machining",
        ),

        (
            "FABRICATION",
            "Fabrication",
        ),

        (
            "SURFACE_TREATMENT",
            "Surface Treatment",
        ),

        (
            "HEAT_TREATMENT",
            "Heat Treatment",
        ),

        (
            "INSPECTION",
            "Inspection / Testing",
        ),

        (
            "PACKAGING",
            "Packaging",
        ),

        (
            "TRANSPORTATION",
            "Transportation / Logistics",
        ),
    ]

    profile = models.ForeignKey(
        VendorProfile,
        on_delete=models.CASCADE,
        related_name="service_categories",
    )

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
    )

    is_primary = models.BooleanField(
        default=False,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "profile",
                    "category",
                ],
                name="unique_vendor_service_category",
            )
        ]

    def __str__(self):

        return (
            f"{self.profile.company_name} - "
            f"{self.get_category_display()}"
        )
# ==========================================================
# VENDOR PROCESS CAPABILITY
# ==========================================================
class VendorProcessCapability(models.Model):

    PROCESS_CHOICES = [
        ("TURNING", "Turning"),
        ("MILLING", "Milling"),
        ("VMC", "VMC"),
        ("HMC", "HMC"),
        ("CNC", "CNC"),
        ("GRINDING", "Grinding"),
        ("EDM", "EDM"),
        ("WIRE_CUT", "Wire Cut"),
        ("FABRICATION", "Fabrication"),
        ("WELDING", "Welding"),
        ("LASER_CUTTING", "Laser Cutting"),
        ("HEAT_TREATMENT", "Heat Treatment"),
        ("HARDENING", "Hardening"),
        ("ANNEALING", "AnneALING"),
        ("COATING", "Coating"),
        ("ANODIZING", "Anodizing"),
        ("PLATING", "Plating"),
        ("PAINTING", "Painting"),
        ("SHOT_BLASTING", "Shot Blasting"),
        ("INSPECTION", "Inspection"),
        ("ASSEMBLY", "Assembly"),
        ("PACKAGING", "Packaging"),
        ("TRANSPORTATION", "Transportation"),
        ("OTHER", "Other"),
    ]

    profile = models.ForeignKey(
        VendorProfile,
        on_delete=models.CASCADE,
        related_name="process_capabilities",
    )

    process_type = models.CharField(
        max_length=50,
        choices=PROCESS_CHOICES,
    )

    capability_description = models.TextField(
        blank=True,
    )

    tolerance_capability = models.CharField(
        max_length=150,
        blank=True,
    )

    material_experience = models.CharField(
        max_length=255,
        blank=True,
    )

    is_verified = models.BooleanField(
        default=False,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "profile",
                    "process_type",
                ],
                name="unique_vendor_process_capability",
            )
        ]

    def __str__(self):

        return (
            f"{self.profile.company_name} - "
            f"{self.get_process_type_display()}"
        )


# ==========================================================
# VENDOR MACHINE
# ==========================================================


class VendorMachine(models.Model):

    profile = models.ForeignKey(
        VendorProfile,
        on_delete=models.CASCADE,
        related_name="machines",
    )

    machine_name = models.CharField(
        max_length=255,
    )

    machine_type = models.CharField(
        max_length=100,
    )

    manufacturer = models.CharField(
        max_length=150,
        blank=True,
    )

    model_number = models.CharField(
        max_length=150,
        blank=True,
    )

    controller = models.CharField(
        max_length=150,
        blank=True,
    )

    work_envelope = models.CharField(
        max_length=255,
        blank=True,
    )

    accuracy = models.CharField(
        max_length=150,
        blank=True,
    )

    maximum_load = models.CharField(
        max_length=150,
        blank=True,
    )

    is_verified = models.BooleanField(
        default=False,
    )

    is_active = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):

        return (
            f"{self.profile.company_name} - "
            f"{self.machine_name}"
        )
# ==========================================================
# MACHINE PROCESS CAPABILITY
# ==========================================================


class VendorMachineProcess(models.Model):

    machine = models.ForeignKey(
        VendorMachine,
        on_delete=models.CASCADE,
        related_name="processes",
    )

    process_type = models.CharField(
        max_length=50,
        choices=VendorProcessCapability.PROCESS_CHOICES,
    )

    is_verified = models.BooleanField(
        default=False,
    )

    def __str__(self):

        return (
            f"{self.machine.machine_name} - "
            f"{self.get_process_type_display()}"
        )
# ==========================================================
# MACHINE AVAILABILITY
# ==========================================================


class VendorMachineAvailability(models.Model):

    machine = models.ForeignKey(
        VendorMachine,
        on_delete=models.CASCADE,
        related_name="availability_slots",
    )

    available_from = models.DateTimeField()

    available_until = models.DateTimeField(
        null=True,
        blank=True,
    )

    is_available = models.BooleanField(
        default=True,
    )

    notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        ordering = [
            "available_from",
        ]

    def __str__(self):

        return (
            f"{self.machine.machine_name} - "
            f"{self.available_from}"
        )
# ==========================================================
# REQUIREMENT PROCESS
# ==========================================================


class RequirementProcess(models.Model):

    PROCESS_CHOICES = [
        ("TURNING", "Turning"),
        ("MILLING", "Milling"),
        ("VMC", "VMC"),
        ("HMC", "HMC"),
        ("CNC", "CNC"),
        ("GRINDING", "Grinding"),
        ("EDM", "EDM"),
        ("WIRE_CUT", "Wire Cut"),
        ("FABRICATION", "Fabrication"),
        ("WELDING", "Welding"),
        ("LASER_CUTTING", "Laser Cutting"),
        ("HEAT_TREATMENT", "Heat Treatment"),
        ("HARDENING", "Hardening"),
        ("ANNEALING", "Annealing"),
        ("COATING", "Coating"),
        ("ANODIZING", "Anodizing"),
        ("PLATING", "Plating"),
        ("PAINTING", "Painting"),
        ("SHOT_BLASTING", "Shot Blasting"),
        ("INSPECTION", "Inspection"),
        ("ASSEMBLY", "Assembly"),
        ("PACKAGING", "Packaging"),
        ("TRANSPORTATION", "Transportation"),
        ("OTHER", "Other"),
    ]

    cad_model = models.ForeignKey(
        CADModel,
        on_delete=models.CASCADE,
        related_name="requirement_processes",
    )

    sequence = models.PositiveIntegerField(
        default=1,
    )

    process_type = models.CharField(
        max_length=50,
        choices=PROCESS_CHOICES,
    )

    process_name = models.CharField(
        max_length=150,
        blank=True,
    )

    quantity = models.PositiveIntegerField(
        default=1,
    )

    material_required = models.BooleanField(
        default=False,
    )

    material_description = models.TextField(
        blank=True,
    )

    drawing_reference = models.CharField(
        max_length=255,
        blank=True,
    )

    technical_specification = models.TextField(
        blank=True,
    )

    tolerance_requirement = models.CharField(
        max_length=255,
        blank=True,
    )

    surface_finish_requirement = models.CharField(
        max_length=255,
        blank=True,
    )

    machine_requirement = models.CharField(
        max_length=255,
        blank=True,
    )

    estimated_process_days = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    is_mandatory = models.BooleanField(
        default=True,
    )

    is_outsourcable = models.BooleanField(
        default=True,
    )

    notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        ordering = [
            "sequence",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "cad_model",
                    "sequence",
                ],
                name="unique_requirement_process_sequence",
            )
        ]

    def __str__(self):

        return (
            f"{self.cad_model.tracking_number} - "
            f"{self.sequence}. "
            f"{self.process_name or self.get_process_type_display()}"
        )
# ==========================================================
# PROCESS BID
# ==========================================================


class ProcessBid(models.Model):

    requirement_process = models.ForeignKey(
        RequirementProcess,
        on_delete=models.CASCADE,
        related_name="process_bids",
    )

    vendor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="process_bids",
    )

    capability = models.ForeignKey(
        VendorProcessCapability,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="process_bids",
    )

    machine = models.ForeignKey(
        VendorMachine,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="process_bids",
    )

    offered_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    delivery_days = models.PositiveIntegerField()

    machine_available_from = models.DateTimeField(
        null=True,
        blank=True,
    )

    material_included = models.BooleanField(
        default=False,
    )

    material_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )

    transportation_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )

    tooling_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )

    inspection_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )

    proposal_notes = models.TextField(
        blank=True,
    )

    is_lumpsum_offer = models.BooleanField(
        default=False,
    )

    status = models.CharField(
        max_length=30,
        default="SUBMITTED",
        choices=[
            ("SUBMITTED", "Submitted"),
            ("SHORTLISTED", "Shortlisted"),
            ("SELECTED", "Selected"),
            ("REJECTED", "Rejected"),
        ],
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def __str__(self):

        return (
            f"{self.vendor.company_name} - "
            f"{self.requirement_process}"
        )