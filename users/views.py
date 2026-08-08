
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required

from .forms import (
    OEMRegistrationForm,
    VendorRegistrationForm,
    VendorProfileForm,
    OEMProfileForm,
)


def terms_conditions(request):
    return render(request, 'users/terms_conditions.html')


def register_oem(request):
    if request.method == "POST":
        form = OEMRegistrationForm(request.POST)
        profile_form = OEMProfileForm(request.POST)

        if form.is_valid() and profile_form.is_valid():
            user = form.save(commit=False)
            user.role = "OEM"
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()

            login(request, user)

            return redirect("oem_dashboard")

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


def register_vendor(request):
    if request.method == "POST":
        form = VendorRegistrationForm(request.POST)
        profile_form = VendorProfileForm(request.POST, request.FILES)

        if form.is_valid() and profile_form.is_valid():
            user = form.save(commit=False)
            user.role = "VENDOR"
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()

            login(request, user)

            return redirect("vendor_dashboard")

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


@login_required
def dashboard(request):
    """
    Central dashboard router.
    """

    user = request.user

    if user.is_superuser or user.role == "ENGINEER":
        return redirect("engineer_dashboard")

    if user.role == "OEM":
        return redirect("oem_dashboard")

    if user.role == "VENDOR":
        return redirect("vendor_dashboard")

    logout(request)
    return redirect("login")


def logout_user(request):
    logout(request)
    return redirect("login")
