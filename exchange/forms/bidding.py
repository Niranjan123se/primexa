from decimal import Decimal

from django import forms

from ..models import Bid

COST_FIELDS = [
    "material_cost",
    "labour_cost",
    "machine_cost",
    "quality_assurance_cost",
    "tooling_cost",
    "development_cost",
    "prototype_cost",
    "production_cost",
    "packaging_and_transport_cost",
    "overhead_cost",
    "other_cost",
]


class BidForm(forms.ModelForm):
    COST_FIELDS = COST_FIELDS

    class Meta:
        model = Bid
        fields = [
            "offered_price",
            *COST_FIELDS,
            "other_cost_description",
            "delivery_days",
            "proposal_notes",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():

            field.widget.attrs["class"] = (
                "form-control bg-light border-0 shadow-sm"
            )

            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs["rows"] = 3

        for field_name in self.COST_FIELDS:
            self.fields[field_name].min_value = Decimal("0.00")
            self.fields[field_name].widget.attrs.update(
                {"class": "form-control bg-light border-0 shadow-sm cost-component", "min": "0", "step": "0.01"}
            )

        self.fields["offered_price"].min_value = Decimal("0.00")
        self.fields["offered_price"].widget.attrs.update({"min": "0", "step": "0.01"})

    @property
    def cost_breakdown_fields(self):
        return [self[field_name] for field_name in self.COST_FIELDS]

    def clean(self):
        cleaned_data = super().clean()
        offered_price = cleaned_data.get("offered_price")
        components = [cleaned_data.get(field_name) for field_name in self.COST_FIELDS]

        if offered_price is not None and all(value is not None for value in components):
            breakdown_total = sum(components, Decimal("0.00"))
            if breakdown_total != offered_price:
                raise forms.ValidationError(
                    "The total cost break-up must exactly equal the offered price."
                )

        if (
            cleaned_data.get("other_cost", Decimal("0.00")) > 0
            and not cleaned_data.get("other_cost_description")
        ):
            self.add_error(
                "other_cost_description",
                "Describe the other cost or fee."
            )

        return cleaned_data

