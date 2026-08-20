from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required

from .forms import (
    OEMRegistrationForm,
    VendorRegistrationForm,
    UserProfileForm,
    VendorProfileForm,
    OEMProfileForm,
)


# ==========================================================
# TERMS & CONDITIONS
# ==========================================================

def terms_conditions(request):
    return render(
        request,
        "users/terms_conditions.html",
    )


# ==========================================================
# OEM REGISTRATION
# ==========================================================

def register_oem(request):

    if request.method == "POST":

        form = OEMRegistrationForm(
            request.POST
        )

        profile_form = OEMProfileForm(
            request.POST
        )

        if (
            form.is_valid()
            and profile_form.is_valid()
        ):

            user = form.save(
                commit=False
            )

            user.role = "OEM"
            user.save()

            profile = profile_form.save(
                commit=False
            )

            profile.user = user
            profile.save()

            login(
                request,
                user,
            )

            return redirect(
                "oem_dashboard"
            )

    else:

        form = OEMRegistrationForm()
        profile_form = OEMProfileForm()

    return render(
        request,
        "users/register_oem.html",
        {
            "form": form,
            "profile_form": profile_form,
        },
    )


# ==========================================================
# VENDOR REGISTRATION
# ==========================================================

def register_vendor(request):

    if request.method == "POST":

        form = VendorRegistrationForm(
            request.POST
        )

        profile_form = VendorProfileForm(
            request.POST,
            request.FILES,
        )

        if (
            form.is_valid()
            and profile_form.is_valid()
        ):

            user = form.save(
                commit=False
            )

            user.role = "VENDOR"
            user.save()

            profile = profile_form.save(
                commit=False
            )

            profile.user = user
            profile.save()

            login(
                request,
                user,
            )

            return redirect(
                "vendor_dashboard"
            )

    else:

        form = VendorRegistrationForm()
        profile_form = VendorProfileForm()

    return render(
        request,
        "users/register_vendor.html",
        {
            "form": form,
            "profile_form": profile_form,
        },
    )


# ==========================================================
# CENTRAL DASHBOARD ROUTER
# ==========================================================

@login_required
def dashboard(request):

    user = request.user

    if (
        user.is_superuser
        or user.role == "ENGINEER"
    ):
        return redirect(
            "engineer_dashboard"
        )

    if user.role == "OEM":
        return redirect(
            "oem_dashboard"
        )

    if user.role == "VENDOR":
        return redirect(
            "vendor_dashboard"
        )

    logout(request)

    return redirect(
        "login"
    )


# ==========================================================
# PROFILE
# ==========================================================

@login_required
def profile(request):
    """
    Central profile page.

    OEM:
        UserProfileForm + OEMProfileForm

    Vendor:
        UserProfileForm + VendorProfileForm

    Engineer:
        Basic UserProfileForm only.
    """

    user = request.user

    # ======================================================
    # VENDOR
    # ======================================================

    if user.role == "VENDOR":

        try:
            vendor_profile = user.vendor_profile

        except Exception:

            from .models import VendorProfile

            vendor_profile = VendorProfile.objects.create(
                user=user
            )

        if request.method == "POST":

            user_form = UserProfileForm(
                request.POST,
                instance=user,
            )

            profile_form = VendorProfileForm(
                request.POST,
                request.FILES,
                instance=vendor_profile,
            )

            if (
                user_form.is_valid()
                and profile_form.is_valid()
            ):

                user_form.save()

                profile_form.save()

                return redirect(
                    "profile"
                )

        else:

            user_form = UserProfileForm(
                instance=user,
            )

            profile_form = VendorProfileForm(
                instance=vendor_profile,
            )

        return render(
            request,
            "users/vendor_profile.html",
            {
                "user_form": user_form,
                "profile_form": profile_form,
                "profile_type": "VENDOR",
                "profile_object": vendor_profile,
            },
        )

    # ======================================================
    # OEM
    # ======================================================

    if user.role == "OEM":

        try:
            oem_profile = user.oem_profile

        except Exception:

            from .models import OEMProfile

            oem_profile = OEMProfile.objects.create(
                user=user
            )

        if request.method == "POST":

            user_form = UserProfileForm(
                request.POST,
                instance=user,
            )

            profile_form = OEMProfileForm(
                request.POST,
                instance=oem_profile,
            )

            if (
                user_form.is_valid()
                and profile_form.is_valid()
            ):

                user_form.save()

                profile_form.save()

                return redirect(
                    "profile"
                )

        else:

            user_form = UserProfileForm(
                instance=user,
            )

            profile_form = OEMProfileForm(
                instance=oem_profile,
            )

        return render(
            request,
            "users/oem_profile.html",
            {
                "user_form": user_form,
                "profile_form": profile_form,
                "profile_type": "OEM",
                "profile_object": oem_profile,
            },
        )

    # ======================================================
    # ENGINEER / SUPERUSER
    # ======================================================

    if request.method == "POST":

        user_form = UserProfileForm(
            request.POST,
            instance=user,
        )

        if user_form.is_valid():

            user_form.save()

            return redirect(
                "profile"
            )

    else:

        user_form = UserProfileForm(
            instance=user,
        )

    return render(
        request,
        "users/profile.html",
        {
            "user_form": user_form,
            "profile_type": "ENGINEER",
        },
    )


# ==========================================================
# LOGOUT
# ==========================================================

def logout_user(request):

    logout(request)

    return redirect(
        "login"
    )