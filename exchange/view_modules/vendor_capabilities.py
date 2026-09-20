from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from users.models import VendorProfile

from ..forms.vendor_capabilities import VendorMachineForm, VendorPortfolioItemForm
from ..models import VendorMachine, VendorShopPhoto


def _vendor_profile_for(request):
    profile, _ = VendorProfile.objects.get_or_create(user=request.user)
    return profile


@login_required
def vendor_machine_management(request, machine_id=None):
    if request.user.role != "VENDOR" and not request.user.is_superuser:
        return HttpResponseForbidden("Only vendors can manage machine capabilities.")

    profile = _vendor_profile_for(request)
    machine = (
        get_object_or_404(VendorMachine, id=machine_id, profile=profile)
        if machine_id is not None else None
    )
    form = VendorMachineForm(request.POST or None, instance=machine)
    if request.method == "POST" and form.is_valid():
        saved_machine = form.save(commit=False)
        saved_machine.profile = profile
        saved_machine.save()
        return redirect("vendor_machine_management")

    return render(request, "exchange/vendor_machine_management.html", {
        "form": form,
        "machine": machine,
        "machines": VendorMachine.objects.filter(profile=profile).order_by(
            "machine_type", "machine_name"
        ),
    })


@login_required
def delete_vendor_machine(request, machine_id):
    if request.user.role != "VENDOR" and not request.user.is_superuser:
        return HttpResponseForbidden("Only vendors can manage machine capabilities.")
    if request.method != "POST":
        return HttpResponseBadRequest("Machine deletion must use POST.")

    get_object_or_404(
        VendorMachine, id=machine_id, profile=_vendor_profile_for(request)
    ).delete()
    return redirect("vendor_machine_management")


@login_required
def vendor_portfolio_management(request, photo_id=None):
    if request.user.role != "VENDOR" and not request.user.is_superuser:
        return HttpResponseForbidden("Only vendors can manage their gallery.")

    profile = _vendor_profile_for(request)
    item = (
        get_object_or_404(VendorShopPhoto, id=photo_id, profile=profile)
        if photo_id is not None else None
    )
    form = VendorPortfolioItemForm(request.POST or None, request.FILES or None, instance=item)
    if request.method == "POST" and form.is_valid():
        saved_item = form.save(commit=False)
        saved_item.profile = profile
        # Public entries are reviewed by Primexa before being displayed.
        if item is None:
            saved_item.is_approved = False
        saved_item.save()
        return redirect("vendor_portfolio_management")

    return render(request, "exchange/vendor_portfolio_management.html", {
        "form": form,
        "item": item,
        "items": VendorShopPhoto.objects.filter(profile=profile),
    })


@login_required
def delete_vendor_portfolio_item(request, photo_id):
    if request.user.role != "VENDOR" and not request.user.is_superuser:
        return HttpResponseForbidden("Only vendors can manage their gallery.")
    if request.method != "POST":
        return HttpResponseBadRequest("Gallery deletion must use POST.")
    get_object_or_404(VendorShopPhoto, id=photo_id, profile=_vendor_profile_for(request)).delete()
    return redirect("vendor_portfolio_management")
