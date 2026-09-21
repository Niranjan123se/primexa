from django import forms
from django.contrib.auth import get_user_model

from ..models import CADModel

User = get_user_model()

class CADUploadForm(forms.ModelForm):
    targeted_vendors = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select bg-light border-0 shadow-sm", "size": "5"}),
        help_text="Direct RFQ: OEMs can select 1 to 5 targeted vendors (or leave blank to publish to open network).",
    )

    class Meta:
        model = CADModel
        fields = [
            "title",
            "sourcing_flow",
            "targeted_vendors",
            "description",
            "file",
            "job_category",
            "work_nature",
            "batch_quantity",
            "target_price",
            "vendor_qualifications_required",
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.user = user
        from users.models import User
        self.fields["targeted_vendors"].queryset = User.objects.filter(
            role="VENDOR", vendor_profile__is_verified=True
        ).order_by("company_name", "username")

        for name, field in self.fields.items():
            if name == "targeted_vendors":
                continue
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = "form-select bg-light border-0 shadow-sm"
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs["class"] = "form-control bg-light border-0 shadow-sm"
            else:
                field.widget.attrs["class"] = "form-control bg-light border-0 shadow-sm"

            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs["rows"] = 3

    def clean_targeted_vendors(self):
        vendors = self.cleaned_data.get("targeted_vendors")
        if vendors and self.user and getattr(self.user, "role", "") == "OEM":
            if len(vendors) > 5:
                raise forms.ValidationError("Security Control: OEMs can select at most 5 targeted vendors per RFQ.")
        return vendors

class EngineerReviewForm(forms.ModelForm):
    class Meta:
        model = CADModel
        fields = [
            "status",
            "expected_delivery_date",
            "fai_remarks",
        ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():

            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = (
                    "form-select bg-light border-0 shadow-sm"
                )

            elif isinstance(field.widget, forms.DateInput):
                field.widget.attrs["class"] = (
                    "form-control bg-light border-0 shadow-sm"
                )
                field.widget.attrs["type"] = "date"

            else:
                field.widget.attrs["class"] = (
                    "form-control bg-light border-0 shadow-sm"
                )

            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs["rows"] = 3
    