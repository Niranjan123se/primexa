from django import forms
from django.utils import timezone

from ..models import DeliveryRiskAlert


class DeliveryRiskForm(forms.ModelForm):

    class Meta:
        model = DeliveryRiskAlert

        fields = [
            "revised_delivery_date",
            "reason",
            "production_status",
            "quantity_completed",
            "issue_description",
            "supporting_document",
        ]

        widgets = {
            "revised_delivery_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": (
                        "form-control "
                        "bg-light "
                        "border-0 "
                        "shadow-sm"
                    ),
                }
            ),

            "reason": forms.Select(
                attrs={
                    "class": (
                        "form-select "
                        "bg-light "
                        "border-0 "
                        "shadow-sm"
                    ),
                }
            ),

            "production_status": forms.Select(
                attrs={
                    "class": (
                        "form-select "
                        "bg-light "
                        "border-0 "
                        "shadow-sm"
                    ),
                }
            ),

            "quantity_completed": forms.NumberInput(
                attrs={
                    "class": (
                        "form-control "
                        "bg-light "
                        "border-0 "
                        "shadow-sm"
                    ),
                    "min": 0,
                }
            ),

            "issue_description": forms.Textarea(
                attrs={
                    "class": (
                        "form-control "
                        "bg-light "
                        "border-0 "
                        "shadow-sm"
                    ),
                    "rows": 5,
                    "placeholder": (
                        "Explain what happened, "
                        "what is causing the delay and "
                        "what support may be required."
                    ),
                }
            ),

            "supporting_document": forms.ClearableFileInput(
                attrs={
                    "class": (
                        "form-control "
                        "bg-light "
                        "border-0 "
                        "shadow-sm"
                    ),
                }
            ),
        }

    def __init__(
        self,
        *args,
        original_delivery_date=None,
        maximum_quantity=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        self.original_delivery_date = original_delivery_date
        self.maximum_quantity = maximum_quantity

        # ------------------------------------------------------
        # Explicit requirements
        # ------------------------------------------------------

        self.fields[
            "revised_delivery_date"
        ].required = True

        self.fields[
            "reason"
        ].required = True

        self.fields[
            "production_status"
        ].required = True

        self.fields[
            "quantity_completed"
        ].required = True

        self.fields[
            "issue_description"
        ].required = True

    # ==========================================================
    # REVISED DELIVERY DATE
    # ==========================================================

    def clean_revised_delivery_date(self):

        revised_date = self.cleaned_data.get(
            "revised_delivery_date"
        )

        if not revised_date:
            raise forms.ValidationError(
                "Please provide the expected revised delivery date."
            )

        if self.original_delivery_date:

            if revised_date <= self.original_delivery_date:

                raise forms.ValidationError(
                    "The revised delivery date must be later "
                    "than the original committed delivery date."
                )

        if revised_date < timezone.localdate():

            raise forms.ValidationError(
                "The revised delivery date cannot be in the past."
            )

        return revised_date

    # ==========================================================
    # COMPLETED QUANTITY
    # ==========================================================

    def clean_quantity_completed(self):

        quantity = self.cleaned_data.get(
            "quantity_completed"
        )

        if quantity is None:

            raise forms.ValidationError(
                "Please enter the quantity completed."
            )

        if quantity < 0:

            raise forms.ValidationError(
                "Completed quantity cannot be negative."
            )

        if (
            self.maximum_quantity is not None
            and quantity > self.maximum_quantity
        ):

            raise forms.ValidationError(
                "Completed quantity cannot exceed "
                f"{self.maximum_quantity}."
            )

        return quantity