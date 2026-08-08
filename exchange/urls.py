from django.urls import path

from . import views

urlpatterns = [


path(
    "",
    views.dashboard,
    name="dashboard"
),

path(
    "oem/",
    views.oem_dashboard,
    name="oem_dashboard"
),

path(
    "vendor/",
    views.vendor_dashboard,
    name="vendor_dashboard"
),

path(
    "engineer/",
    views.engineer_dashboard,
    name="engineer_dashboard"
),

path(
    "upload/",
    views.upload_job_view,
    name="upload_job"
),

path(
    "nda/<uuid:file_id>/",
    views.sign_nda,
    name="sign_nda"
),

path(
    "download/<uuid:file_id>/",
    views.download_file,
    name="download_file"
),

path(
    "download-nda/<uuid:file_id>/",
    views.download_nda_pdf,
    name="download_nda_pdf"
),

path(
    "review/<uuid:file_id>/",
    views.review_workload,
    name="review_workload"
),

path(
    "bid/<uuid:file_id>/",
    views.place_bid_view,
    name="place_bid"
),

path(
    "manage-bids/<uuid:file_id>/",
    views.primexa_manage_bids,
    name="primexa_manage_bids"
),

# OEM COMMERCIAL APPROVAL

path(
    "oem-approve/<uuid:file_id>/",
    views.oem_approve_quote,
    name="oem_approve_quote"
),

# FINAL VENDOR AWARD

path(
    "final-award/<uuid:file_id>/",
    views.final_vendor_award,
    name="final_vendor_award"
),

]
