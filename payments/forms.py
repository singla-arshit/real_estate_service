from django import forms
from django.utils import timezone
from .models import Payment, Notice, PaymentDetail
from properties.models import RentalAgreement

class PaymentForm(forms.ModelForm):
    """Form for creating and editing payments."""
    payment_date = forms.DateField(
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={
                'type': 'date',
                'class': 'form-control',
                'value': timezone.now().strftime('%Y-%m-%d')
            }
        ),
        input_formats=['%Y-%m-%d'],
        initial=timezone.now().date()
    )
    
    due_date = forms.DateField(
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={
                'type': 'date',
                'class': 'form-control',
                'value': timezone.now().strftime('%Y-%m-%d')
            }
        ),
        input_formats=['%Y-%m-%d'],
        initial=timezone.now().date()
    )
    
    class Meta:
        model = Payment
        fields = ['rental_agreement', 'amount', 'payment_date', 'due_date', 'payment_method', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'rental_agreement': forms.Select(attrs={'class': 'form-select'})
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
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.pk:
            # For existing notices, disable editing of rental_agreement
            self.fields['rental_agreement'].disabled = True
        elif self.user:
            if self.user.is_landlord:
                # Landlords can only create notices for their own rental agreements
                self.fields['rental_agreement'].queryset = RentalAgreement.objects.filter(
                    property__landlord=self.user.landlord_profile, 
                    status='active'
                )
            elif self.user.is_tenant:
                # Tenants can only create notices for their own rental agreements
                self.fields['rental_agreement'].queryset = RentalAgreement.objects.filter(
                    tenant=self.user.tenant_profile, 
                    status='active'
                )
    
    def clean(self):
        cleaned_data = super().clean()
        rental_agreement = cleaned_data.get('rental_agreement')
        
        if rental_agreement and self.user:
            if self.user.is_landlord:
                cleaned_data['sender_landlord'] = self.user.landlord_profile
                cleaned_data['recipient_tenant'] = rental_agreement.tenant
            elif self.user.is_tenant:
                cleaned_data['sender_tenant'] = self.user.tenant_profile
                cleaned_data['recipient_landlord'] = rental_agreement.property.landlord
                
        return cleaned_data

class PaymentDetailForm(forms.ModelForm):
    """Form for managing payment details for a property."""
    class Meta:
        model = PaymentDetail
        fields = ['payment_method', 'account_holder_name', 'bank_name', 'account_number', 
                 'ifsc_code', 'upi_id', 'upi_qr_code', 'additional_instructions']
        widgets = {
            'additional_instructions': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        property_obj = kwargs.pop('property_obj', None)
        super().__init__(*args, **kwargs)
        if property_obj:
            self.instance.property = property_obj