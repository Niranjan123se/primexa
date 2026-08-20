from django import forms

from ..models import Bid

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = [
        "offered_price",
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

