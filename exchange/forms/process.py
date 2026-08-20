from django import forms

from ..models import RequirementProcess


class RequirementProcessForm(forms.ModelForm):
    """
    Form used by the OEM to define one manufacturing
    process within a manufacturing requirement.
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
                    "placeholder": "1",
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
                    "placeholder": (
                        "Example: Precision CNC Turning"
                    ),
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
                    "placeholder": (
                        "Example: EN8 steel, 42 mm bar"
                    ),
                }
            ),

            "drawing_reference": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Drawing number / revision"
                    ),
                }
            ),

            "technical_specification": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": (
                        "Enter technical requirements "
                        "for this process."
                    ),
                }
            ),

            "tolerance_requirement": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Example: ±0.02 mm"
                    ),
                }
            ),

            "surface_finish_requirement": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Example: Ra 1.6"
                    ),
                }
            ),

            "machine_requirement": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": (
                        "Example: 5-axis VMC / CNC Turning"
                    ),
                }
            ),

            "estimated_process_days": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                    "placeholder": "Estimated days",
                }
            ),

            "is_mandatory": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                    "checked": True,
                }
            ),

            "is_outsourcable": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                    "checked": True,
                }
            ),

            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": (
                        "Additional process instructions."
                    ),
                }
            ),
        }

    def clean_sequence(self):
        sequence = self.cleaned_data["sequence"]

        if sequence < 1:
            raise forms.ValidationError(
                "Process sequence must start from 1."
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
                "Estimated process duration must be at least 1 day."
            )

        return days