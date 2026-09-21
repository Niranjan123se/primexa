from django.urls import path
from django.contrib.auth import views as auth_views

from . import views


urlpatterns = [

    path(
        "",
        views.dashboard,
        name="dashboard"
    ),

    path(
    "profile/",
    views.profile,
    name="profile",
    ),

    path(
        "register/oem/",
        views.register_oem,
        name="register_oem"
    ),
    

    path(
        "register/vendor/",
        views.register_vendor,
        name="register_vendor"
    ),

    path("register/expert/", views.register_expert, name="register_expert"),
    path("expert/dashboard/", views.expert_dashboard, name="expert_dashboard"),
    path("request-service/", views.request_service, name="request_service"),
    path("experts/", views.expert_directory, name="expert_directory"),
    path("experts/<slug:slug>/", views.public_expert_profile, name="public_expert_profile"),
    path("experts/id/<int:expert_id>/", views.public_expert_profile, name="public_expert_profile_by_id"),
    path("expert/photo/add/", views.add_expert_photo, name="add_expert_photo"),
    path("expert/photo/<int:photo_id>/delete/", views.delete_expert_photo, name="delete_expert_photo"),
    path("expert/certificate/add/", views.add_expert_certificate, name="add_expert_certificate"),
    path("expert/certificate/<int:cert_id>/delete/", views.delete_expert_certificate, name="delete_expert_certificate"),
    path("expert/request/<int:request_id>/respond/", views.expert_respond_service_request, name="expert_respond_service_request"),
    path("engineer/bulk-invite-experts/", views.engineer_bulk_invite_experts, name="engineer_bulk_invite_experts"),
    path("engineer/user/<int:user_id>/toggle-active/", views.toggle_user_active_status, name="toggle_user_active_status"),
    path("engineer/user/<int:user_id>/delete/", views.delete_user_account, name="delete_user_account"),

    path(
        "terms-conditions/",
        views.terms_conditions,
        name="terms_conditions"
    ),

    # ======================================================
    # LOGIN
    # ======================================================

    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="users/login.html"
        ),
        name="login"
    ),

    # ======================================================
    # LOGOUT
    # ======================================================

    path(
        "logout/",
        views.logout_user,
        name="logout"
    ),

    # ======================================================
    # PASSWORD RESET
    # ======================================================

    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="users/password_reset.html",
            email_template_name="users/password_reset_email.txt",
            html_email_template_name="users/password_reset_email.html",
            subject_template_name="users/password_reset_subject.txt",
            success_url="/password-reset/done/",
        ),
        name="password_reset"
    ),

    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="users/password_reset_done.html"
        ),
        name="password_reset_done"
    ),

    path(
        "password-reset-confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="users/password_reset_confirm.html",
            success_url="/password-reset/complete/",
        ),
        name="password_reset_confirm"
    ),

    path(
        "password-reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="users/password_reset_complete.html"
        ),
        name="password_reset_complete"
    ),

]
