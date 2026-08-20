
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone

from .models import User, VendorProfile, OEMProfile


class OEMRegistrationForm(UserCreationForm):
    company_name = forms.CharField(
        max_length=255,
        required=True,
        label="Company Name"
    )

    phone_number = forms.CharField(
        max_length=20,
        required=True,
        label="Phone Number"
    )

    agree_to_terms = forms.BooleanField(
        required=True,
        label="I agree to the Primexa Global Terms & Conditions and Confidentiality Policy."
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            'username',
            'email',
            'company_name',
            'phone_number',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control bg-light border-0 shadow-sm'

        # Proper checkbox styling
        self.fields['agree_to_terms'].widget.attrs['class'] = 'form-check-input'
        self.fields['agree_to_terms'].widget.attrs['style'] = 'width: 18px; height: 18px;'


    def save(self, commit=True):
        user = super().save(commit=False)

        user.role = 'OEM'
        user.company_name = self.cleaned_data['company_name']
        user.phone_number = self.cleaned_data['phone_number']
        user.accepted_terms_date = timezone.now()

        if commit:
            user.save()

        return user


class VendorRegistrationForm(UserCreationForm):

    company_name = forms.CharField(
        max_length=255,
        required=True,
        label="Company Name"
    )

    phone_number = forms.CharField(
        max_length=20,
        required=True,
        label="Phone Number"
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            'username',
            'email',
            'company_name',
            'phone_number',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control bg-light border-0 shadow-sm'


class VendorProfileForm(forms.ModelForm):

    class Meta:
        model = VendorProfile
        exclude = ['user']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():

            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
                field.widget.attrs['style'] = 'width: 18px; height: 18px;'

            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select bg-light border-0 shadow-sm'

            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs['class'] = 'form-control bg-light border-0 shadow-sm'

            else:
                field.widget.attrs['class'] = 'form-control bg-light border-0 shadow-sm'

            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs['rows'] = 3


class OEMProfileForm(forms.ModelForm):

    class Meta:
        model = OEMProfile
        exclude = ['user']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():

            if isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-select bg-light border-0 shadow-sm'
            else:
                field.widget.attrs['class'] = 'form-control bg-light border-0 shadow-sm'

            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs['rows'] = 3

