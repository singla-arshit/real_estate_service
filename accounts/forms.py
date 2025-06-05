from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Landlord, Tenant


class UserRegistrationForm(forms.ModelForm):
    """Form for user registration."""
    password = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Repeat password', widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'profile_picture']
    
    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Passwords don\'t match.')
        return cd['password2']
    
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email already in use.')
        return email


class LandlordRegistrationForm(forms.ModelForm):
    """Form for landlord registration."""
    class Meta:
        model = Landlord
        fields = ['company_name', 'address', 'tax_id']


class TenantRegistrationForm(forms.ModelForm):
    """Form for tenant registration."""
    class Meta:
        model = Tenant
        fields = ['address', 'id_proof', 'employment_status', 'emergency_contact']


class UserEditForm(forms.ModelForm):
    """Form for editing user information."""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'profile_picture']


class LandlordEditForm(forms.ModelForm):
    """Form for editing landlord information."""
    class Meta:
        model = Landlord
        fields = ['company_name', 'address', 'tax_id']


class TenantEditForm(forms.ModelForm):
    """Form for editing tenant information."""
    class Meta:
        model = Tenant
        fields = ['address', 'id_proof', 'employment_status', 'emergency_contact']