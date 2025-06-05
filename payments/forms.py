from django import forms
from .models import Payment, Notice
from properties.models import RentalAgreement

class PaymentForm(forms.ModelForm):
    """Form for creating and editing payments."""
    class Meta:
        model = Payment
        fields = ['rental_agreement', 'amount', 'due_date', 'payment_method', 'notes']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        landlord = kwargs.pop('landlord', None)
        super().__init__(*args, **kwargs)
        if landlord:
            # Landlords can only create payments for their own rental agreements
            self.fields['rental_agreement'].queryset = RentalAgreement.objects.filter(
                property__landlord=landlord, status='active'
            )
        elif self.instance and self.instance.pk:
            # For existing payments, disable editing of rental_agreement
            self.fields['rental_agreement'].disabled = True

    def clean_amount(self):
        """Validate that payment amount is positive."""
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero.')
        return amount

class NoticeForm(forms.ModelForm):
    """Form for creating and editing notices."""
    class Meta:
        model = Notice
        fields = ['rental_agreement', 'subject', 'message', 'notice_type']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            if user.is_landlord:
                # Landlords can only create notices for their own rental agreements
                self.fields['rental_agreement'].queryset = RentalAgreement.objects.filter(
                    property__landlord=user.landlord_profile, status='active'
                )
            elif user.is_tenant:
                # Tenants can only create notices for their own rental agreements
                self.fields['rental_agreement'].queryset = RentalAgreement.objects.filter(
                    tenant=user.tenant_profile, status='active'
                )
        elif self.instance and self.instance.pk:
            # For existing notices, disable editing of rental_agreement
            self.fields['rental_agreement'].disabled = True