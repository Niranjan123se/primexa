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
    path("experts/<int:expert_id>/", views.public_expert_profile, name="public_expert_profile"),

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
            email_template_name="users/password_reset_email.html",
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
