from django.urls import path

from . import views

from .view_modules.process import (
    requirement_processes,
    delete_requirement_process,
)

from .view_modules.engineering_process import (
    engineering_process_plan,
    submit_engineering_process_plan,
    review_engineering_process_plan,
    delete_engineering_process,
)
from .view_modules.vendor_capabilities import (
    delete_vendor_machine,
    delete_vendor_portfolio_item,
    vendor_machine_management,
    vendor_portfolio_management,
)


urlpatterns = [

    # ==========================================================
    # DASHBOARD ROUTER
    # ==========================================================

    path(
        "",
        views.dashboard,
        name="dashboard",
    ),

    # ==========================================================
    # OEM DASHBOARD
    # ==========================================================

    path(
        "oem/",
        views.oem_dashboard,
        name="oem_dashboard",
    ),

    # ==========================================================
    # VENDOR DASHBOARD
    # ==========================================================

    path(
        "vendor/",
        views.vendor_dashboard,
        name="vendor_dashboard",
    ),
    path("vendor/machines/", vendor_machine_management, name="vendor_machine_management"),
    path("vendor/machines/<int:machine_id>/", vendor_machine_management, name="edit_vendor_machine"),
    path("vendor/machines/<int:machine_id>/delete/", delete_vendor_machine, name="delete_vendor_machine"),
    path("vendor/gallery/", vendor_portfolio_management, name="vendor_portfolio_management"),
    path("vendor/gallery/<int:photo_id>/", vendor_portfolio_management, name="edit_vendor_portfolio_item"),
    path("vendor/gallery/<int:photo_id>/delete/", delete_vendor_portfolio_item, name="delete_vendor_portfolio_item"),

    # ==========================================================
    # ENGINEER DASHBOARD
    # ==========================================================

    path(
        "engineer/",
        views.engineer_dashboard,
        name="engineer_dashboard",
    ),

    # ==========================================================
    # OEM CREATE MANUFACTURING REQUIREMENT
    # ==========================================================

    path(
        "upload/",
        views.upload_job_view,
        name="upload_job",
    ),

    # ==========================================================
    # NDA
    # ==========================================================

    path(
        "nda/<uuid:file_id>/",
        views.sign_nda,
        name="sign_nda",
    ),

    # ==========================================================
    # SECURE CAD FILE DOWNLOAD
    # ==========================================================

    path(
        "download/<uuid:file_id>/",
        views.download_file,
        name="download_file",
    ),

    # ==========================================================
    # SIGNED NDA PDF DOWNLOAD
    # ==========================================================

    path(
        "download-nda/<uuid:file_id>/",
        views.download_nda_pdf,
        name="download_nda_pdf",
    ),

    # ==========================================================
    # ENGINEER REQUIREMENT REVIEW
    # ==========================================================

    path(
        "review/<uuid:file_id>/",
        views.review_workload,
        name="review_workload",
    ),

    # ==========================================================
    # VENDOR PLACE BID
    # ==========================================================

    path(
        "bid/<uuid:file_id>/",
        views.place_bid_view,
        name="place_bid",
    ),

    # ==========================================================
    # PRIMEXA INTERNAL BID MANAGEMENT
    # ==========================================================

    path(
        "manage-bids/<uuid:file_id>/",
        views.primexa_manage_bids,
        name="primexa_manage_bids",
    ),

    # ==========================================================
    # OEM COMMERCIAL APPROVAL
    # ==========================================================

    path(
        "oem-approve/<uuid:file_id>/",
        views.oem_approve_quote,
        name="oem_approve_quote",
    ),

    # ==========================================================
    # FINAL VENDOR AWARD
    # ==========================================================

    path(
        "final-award/<uuid:file_id>/",
        views.final_vendor_award,
        name="final_vendor_award",
    ),

    # ==========================================================
    # FAI — FIRST ARTICLE INSPECTION
    # ==========================================================

    path(
        "fai/submit/<uuid:file_id>/",
        views.fai_submit,
        name="fai_submit",
    ),

    path(
        "fai/review/<uuid:file_id>/",
        views.fai_review,
        name="fai_review",
    ),

    # ==========================================================
    # DELIVERY RISK
    # ==========================================================

    path(
        "delivery-risk/<uuid:file_id>/",
        views.report_delivery_risk,
        name="report_delivery_risk",
    ),

    path(
        "delivery-risk/review/<int:alert_id>/",
        views.review_delivery_risk,
        name="review_delivery_risk",
    ),

    # ==========================================================
    # NOTIFICATIONS
    # ==========================================================

    path(
        "notifications/",
        views.notifications_page,
        name="notifications",
    ),

    # ==========================================================
    # REQUIREMENT PROCESS PLANNING
    # ==========================================================

    path(
        "requirement/<uuid:file_id>/processes/",
        requirement_processes,
        name="requirement_processes",
    ),

    path(
        "requirement-process/<int:process_id>/delete/",
        delete_requirement_process,
        name="delete_requirement_process",
    ),

    # ==========================================================
    # ENGINEERING PROCESS PLAN
    # ==========================================================

    path(
        "engineering/process-plan/<uuid:file_id>/",
        engineering_process_plan,
        name="engineering_process_plan",
    ),

    # ==========================================================
    # SUBMIT ENGINEERING PROCESS PLAN
    # ==========================================================

    path(
        "engineering/process-plan/<uuid:file_id>/submit/",
        submit_engineering_process_plan,
        name="submit_engineering_process_plan",
    ),

    # ==========================================================
    # REVIEW ENGINEERING PROCESS PLAN
    # ==========================================================

    path(
        "engineering/process-plan/<uuid:file_id>/review/",
        review_engineering_process_plan,
        name="review_engineering_process_plan",
    ),

    # ==========================================================
    # DELETE ENGINEERING PROCESS
    # ==========================================================

    path(
        "engineering/process/<int:process_id>/delete/",
        delete_engineering_process,
        name="delete_engineering_process",
    ),
]
