from django import forms
from .models import CADModel, Bid


class CADUploadForm(forms.ModelForm):
    class Meta:
        model = CADModel
        fields = [
            'title',
            'description',
            'file',
            'job_category',
            'work_nature',
            'batch_quantity',
            'target_price',
            'vendor_qualifications_required',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select bg-light border-0 shadow-sm'
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs['class'] = 'form-control bg-light border-0 shadow-sm'
            else:
                field.widget.attrs['class'] = 'form-control bg-light border-0 shadow-sm'

            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs['rows'] = 3


class EngineerReviewForm(forms.ModelForm):
    class Meta:
        model = CADModel
        fields = [
            'status',
            'expected_delivery_date',
            'fai_remarks',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select bg-light border-0 shadow-sm'
            elif isinstance(field.widget, forms.DateInput):
                field.widget.attrs['class'] = 'form-control bg-light border-0 shadow-sm'
                field.widget.attrs['type'] = 'date'
            else:
                field.widget.attrs['class'] = 'form-control bg-light border-0 shadow-sm'

            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs['rows'] = 3


class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = [
            'offered_price',
            'delivery_days',
            'proposal_notes',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control bg-light border-0 shadow-sm'

            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs['rows'] = 3