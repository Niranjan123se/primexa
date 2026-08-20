from django import forms

from ..models import FAIRecord

class FAISubmissionForm(forms.ModelForm):
    class Meta:
        model = FAIRecord
        fields = [
            "inspection_report",
            "dimensional_report",
            "material_certificate",
            "other_documents",
            "inspection_notes",
    ]


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():

            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs["class"] = (
                    "form-control bg-light border-0 shadow-sm"
                )

            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs["class"] = (
                    "form-control bg-light border-0 shadow-sm"
                )
                field.widget.attrs["rows"] = 4

            else:
                field.widget.attrs["class"] = (
                    "form-control bg-light border-0 shadow-sm"
                )

class FAIReviewForm(forms.ModelForm):
# """
# Primexa Engineer FAI review form.

# Engineers can approve or reject
# the submitted First Article Inspection.
# """

    class Meta:
        model = FAIRecord
        fields = [
            "status",
            "engineer_remarks",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Engineer can only make these two decisions.
        self.fields["status"].choices = [
            ("APPROVED", "Approve FAI"),
            ("REJECTED", "Reject FAI"),
        ]

        for field in self.fields.values():

            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = (
                    "form-select bg-light border-0 shadow-sm"
                )

            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs["class"] = (
                    "form-control bg-light border-0 shadow-sm"
                )
                field.widget.attrs["rows"] = 4

            else:
                field.widget.attrs["class"] = (
                    "form-control bg-light border-0 shadow-sm"
                )

