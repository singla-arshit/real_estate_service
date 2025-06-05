from django import forms
from .models import Property, PropertyImage, RentalAgreement, PropertyRequest


class PropertyForm(forms.ModelForm):
    """Form for creating and editing properties."""
    class Meta:
        model = Property
        fields = [
            'title', 'description', 'property_type', 'address', 'city', 'state',
            'zip_code', 'bedrooms', 'bathrooms', 'area_sqft', 'rent_amount',
            'security_deposit', 'available_from', 'amenities'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'amenities': forms.Textarea(attrs={'rows': 3}),
            'available_from': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_rent_amount(self):
        """Validate that rent amount is positive."""
        rent_amount = self.cleaned_data.get('rent_amount')
        if rent_amount <= 0:
            raise forms.ValidationError('Rent amount must be greater than zero.')
        return rent_amount

    def clean_security_deposit(self):
        """Validate that security deposit is positive."""
        security_deposit = self.cleaned_data.get('security_deposit')
        if security_deposit <= 0:
            raise forms.ValidationError('Security deposit must be greater than zero.')
        return security_deposit


class PropertyImageForm(forms.ModelForm):
    """Form for uploading property images."""
    class Meta:
        model = PropertyImage
        fields = ['image', 'caption', 'is_primary']
        widgets = {
            'caption': forms.TextInput(attrs={'placeholder': 'Brief description of the image'}),
        }


class RentalAgreementForm(forms.ModelForm):
    """Form for creating and editing rental agreements."""
    class Meta:
        model = RentalAgreement
        fields = [
            'start_date', 'end_date', 'rent_amount', 'security_deposit',
            'terms_and_conditions', 'agreement_document'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'terms_and_conditions': forms.Textarea(attrs={'rows': 6}),
        }

    def clean(self):
        """Validate that end date is after start date."""
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date and start_date >= end_date:
            raise forms.ValidationError('End date must be after start date.')

        return cleaned_data


class PropertyRequestForm(forms.ModelForm):
    """Form for tenants to request a property."""
    class Meta:
        model = PropertyRequest
        fields = ['requested_move_in_date', 'message']
        widgets = {
            'requested_move_in_date': forms.DateInput(attrs={'type': 'date'}),
            'message': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell the landlord why you are interested in this property...'}),
        }

    def clean_requested_move_in_date(self):
        """Validate that requested move-in date is not in the past."""
        from django.utils import timezone
        import datetime

        requested_date = self.cleaned_data.get('requested_move_in_date')
        today = timezone.now().date()

        if requested_date < today:
            raise forms.ValidationError('Move-in date cannot be in the past.')

        return requested_date