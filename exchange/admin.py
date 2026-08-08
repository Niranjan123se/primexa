from django.contrib import admin
from .models import CADModel, WorkloadTransfer, Bid


@admin.register(CADModel)
class CADModelAdmin(admin.ModelAdmin):
    list_display = (
        "tracking_number",
        "title",
        "uploaded_by",
        "status",
        "batch_quantity",
        "uploaded_at",
    )

    list_filter = (
        "status",
        "job_category",
        "work_nature",
    )

    search_fields = (
        "tracking_number",
        "title",
        "uploaded_by__username",
        "uploaded_by__company_name",
    )

    readonly_fields = (
        "tracking_number",
        "uploaded_at",
    )


@admin.register(WorkloadTransfer)
class WorkloadTransferAdmin(admin.ModelAdmin):
    list_display = (
        "cad_model",
        "sub_vendor",
        "nda_signed_by_sub",
        "agreed_at",
        "ip_address",
        "signature_hash",
    )

    list_filter = (
        "nda_signed_by_sub",
    )

    search_fields = (
        "cad_model__tracking_number",
        "cad_model__title",
        "sub_vendor__username",
        "sub_vendor__company_name",
    )

    readonly_fields = (
        "signature_hash",
        "agreed_at",
        "ip_address",
    )


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = (
        "cad_model",
        "vendor",
        "offered_price",
        "delivery_days",
        "created_at",
    )

    list_filter = (
        "created_at",
    )

    search_fields = (
        "cad_model__tracking_number",
        "cad_model__title",
        "vendor__username",
        "vendor__company_name",
    )

    readonly_fields = (
        "created_at",
    )