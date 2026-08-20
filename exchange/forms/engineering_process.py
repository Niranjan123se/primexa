from django import forms

from ..models import RequirementProcess, CADModel


class EngineeringProcessForm(forms.ModelForm):
    """
    Primexa Engineer form for creating one manufacturing
    process step in an engineering process plan.
    """

    class Meta:
        model = RequirementProcess

        fields = [
            "sequence",
            "process_type",
            "process_name",
            "quantity",
            "material_required",
            "material_description",
            "drawing_reference",
            "technical_specification",
            "tolerance_requirement",
            "surface_finish_requirement",
            "machine_requirement",
            "estimated_process_days",
            "is_mandatory",
            "is_outsourcable",
            "notes",
        ]

        widgets = {
            "sequence": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                }
            ),

            "process_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),

            "process_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: Precision CNC Turning",
                }
            ),

            "quantity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                }
            ),

            "material_required": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),

            "material_description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Material grade / specification",
                }
            ),

            "drawing_reference": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Drawing number / revision",
                }
            ),

            "technical_specification": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Technical requirements",
                }
            ),

            "tolerance_requirement": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: ±0.02 mm",
                }
            ),

            "surface_finish_requirement": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: Ra 1.6",
                }
            ),

            "machine_requirement": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: 5 Axis VMC",
                }
            ),

            "estimated_process_days": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                }
            ),

            "is_mandatory": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),

            "is_outsourcable": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),

            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Engineering notes",
                }
            ),
        }

    def clean_sequence(self):
        sequence = self.cleaned_data["sequence"]

        if sequence < 1:
            raise forms.ValidationError(
                "Sequence must be at least 1."
            )

        return sequence

    def clean_quantity(self):
        quantity = self.cleaned_data["quantity"]

        if quantity < 1:
            raise forms.ValidationError(
                "Quantity must be at least 1."
            )

        return quantity

    def clean_estimated_process_days(self):
        days = self.cleaned_data.get(
            "estimated_process_days"
        )

        if days is not None and days < 1:
            raise forms.ValidationError(
                "Estimated process days must be at least 1."
            )

        return days


class EngineeringProcessReviewForm(forms.Form):
    """
    Primexa Engineer approval form.
    """

    DECISION_CHOICES = [
        (
            "APPROVE",
            "Approve Process Plan",
        ),
        (
            "REJECT",
            "Reject - Revision Required",
        ),
    ]

    decision = forms.ChoiceField(
        choices=DECISION_CHOICES,
        widget=forms.RadioSelect(
            attrs={
                "class": "form-check-input",
            }
        ),
    )

    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": (
                    "Add engineering review remarks..."
                ),
            }
        ),
    )