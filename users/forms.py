from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone

from .models import (
    User,
    VendorProfile,
    OEMProfile,
    ExpertProfile,
    ServiceRequest,
)


# ==========================================================
# OEM REGISTRATION
# ==========================================================

class OEMRegistrationForm(UserCreationForm):

    company_name = forms.CharField(
        max_length=255,
        required=True,
        label="Company Name",
    )

    phone_number = forms.CharField(
        max_length=20,
        required=True,
        label="Phone Number",
    )

    agree_to_terms = forms.BooleanField(
        required=True,
        label=(
            "I agree to the Primexa Global Terms & Conditions "
            "and Confidentiality Policy."
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "email",
            "company_name",
            "phone_number",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "form-control bg-light border-0 shadow-sm"
            )

        self.fields["agree_to_terms"].widget.attrs["class"] = (
            "form-check-input"
        )

        self.fields["agree_to_terms"].widget.attrs["style"] = (
            "width: 18px; height: 18px;"
        )

    def save(self, commit=True):
        user = super().save(commit=False)

        user.role = "OEM"
        user.company_name = self.cleaned_data["company_name"]
        user.phone_number = self.cleaned_data["phone_number"]
        user.accepted_terms_date = timezone.now()

        if commit:
            user.save()

        return user


# ==========================================================
# VENDOR REGISTRATION
# ==========================================================

class VendorRegistrationForm(UserCreationForm):

    company_name = forms.CharField(
        max_length=255,
        required=True,
        label="Company Name",
    )

    phone_number = forms.CharField(
        max_length=20,
        required=True,
        label="Phone Number",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "email",
            "company_name",
            "phone_number",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "form-control bg-light border-0 shadow-sm"
            )


class ExpertRegistrationForm(OEMRegistrationForm):
    """External expert accounts are deliberately not internal ENGINEER accounts."""

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = "EXPERT"
        if commit:
            user.save()
        return user


# ==========================================================
# USER ACCOUNT / PROFILE FORM
# ==========================================================

class UserProfileForm(forms.ModelForm):
    """
    Allows the logged-in user to edit their own basic account
    information.

    Username and role are intentionally NOT editable.
    """

    class Meta:
        model = User

        fields = [
            "email",
            "company_name",
            "phone_number",
        ]

        labels = {
            "email": "Email Address",
            "company_name": "Company Name",
            "phone_number": "Phone Number",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "form-control bg-light border-0 shadow-sm"
            )


# ==========================================================
# VENDOR PROFILE
# ==========================================================

class VendorProfileForm(forms.ModelForm):

    class Meta:
        model = VendorProfile

        exclude = [
            "user",
            "vendor_id_code",
            "is_public_profile",
            "is_public_profile_approved",
            "is_verified",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():

            if isinstance(
                field.widget,
                forms.CheckboxInput,
            ):
                field.widget.attrs["class"] = (
                    "form-check-input"
                )

                field.widget.attrs["style"] = (
                    "width: 18px; height: 18px;"
                )

            elif isinstance(
                field.widget,
                forms.Select,
            ):
                field.widget.attrs["class"] = (
                    "form-select bg-light border-0 shadow-sm"
                )

            elif isinstance(
                field.widget,
                forms.FileInput,
            ):
                field.widget.attrs["class"] = (
                    "form-control bg-light border-0 shadow-sm"
                )

            else:
                field.widget.attrs["class"] = (
                    "form-control bg-light border-0 shadow-sm"
                )

            if isinstance(
                field.widget,
                forms.Textarea,
            ):
                field.widget.attrs["rows"] = 3


# ==========================================================
# OEM PROFILE
# ==========================================================

class OEMProfileForm(forms.ModelForm):

    class Meta:
        model = OEMProfile

        exclude = [
            "user",
            "oem_id_code",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():

            if isinstance(
                field.widget,
                forms.Select,
            ):
                field.widget.attrs["class"] = (
                    "form-select bg-light border-0 shadow-sm"
                )

            else:
                field.widget.attrs["class"] = (
                    "form-control bg-light border-0 shadow-sm"
                )

            if isinstance(
                field.widget,
                forms.Textarea,
            ):
                field.widget.attrs["rows"] = 3


class ExpertProfileForm(forms.ModelForm):
    class Meta:
        model = ExpertProfile
        exclude = ["user", "expert_id_code", "is_public_profile", "is_verified"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control bg-light border-0 shadow-sm"
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs["rows"] = 3


class ServiceRequestForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = [
            "request_type", "project_title", "task_description", "required_processes",
            "quantity_or_scope", "budget_range", "target_timeline", "contact_name",
            "contact_email", "contact_phone", "company_name",
        ]
        widgets = {
            "task_description": forms.Textarea(attrs={"rows": 4}),
            "required_processes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control bg-light border-0 shadow-sm"
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select bg-light border-0 shadow-sm"
