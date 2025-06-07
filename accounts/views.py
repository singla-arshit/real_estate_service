from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
from django.utils import timezone
from .models import User, Landlord, Tenant
from .forms import UserRegistrationForm, LandlordRegistrationForm, TenantRegistrationForm, UserEditForm, LandlordEditForm, TenantEditForm
from properties.models import Property, RentalAgreement, PropertyRequest
from payments.models import Payment, Notice, PaymentDetail


def register(request):
    """General registration page with options for landlord or tenant registration."""
    return render(request, 'accounts/register.html')


def register_landlord(request):
    """Registration view for landlords."""
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST, request.FILES)
        landlord_form = LandlordRegistrationForm(request.POST)
        
        if user_form.is_valid() and landlord_form.is_valid():
            # Create user but don't save to database yet
            new_user = user_form.save(commit=False)
            new_user.is_landlord = True
            new_user.set_password(user_form.cleaned_data['password'])
            new_user.save()
            
            # Create landlord profile
            landlord = landlord_form.save(commit=False)
            landlord.user = new_user
            landlord.save()
            
            # Log the user in
            login(request, new_user)
            messages.success(request, 'Registration successful! Welcome to Micro Real Estate Management.')
            return redirect('landlord_dashboard')
    else:
        user_form = UserRegistrationForm()
        landlord_form = LandlordRegistrationForm()
    
    return render(request, 'accounts/register_landlord.html', {
        'user_form': user_form,
        'landlord_form': landlord_form
    })


def register_tenant(request):
    """Registration view for tenants."""
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST, request.FILES)
        tenant_form = TenantRegistrationForm(request.POST, request.FILES)
        
        if user_form.is_valid() and tenant_form.is_valid():
            # Create user but don't save to database yet
            new_user = user_form.save(commit=False)
            new_user.is_tenant = True
            new_user.set_password(user_form.cleaned_data['password'])
            new_user.save()
            
            # Create tenant profile
            tenant = tenant_form.save(commit=False)
            tenant.user = new_user
            tenant.save()
            
            # Log the user in
            login(request, new_user)
            messages.success(request, 'Registration successful! Welcome to Micro Real Estate Management.')
            return redirect('tenant_dashboard')
    else:
        user_form = UserRegistrationForm()
        tenant_form = TenantRegistrationForm()
    
    return render(request, 'accounts/register_tenant.html', {
        'user_form': user_form,
        'tenant_form': tenant_form
    })


@login_required
def profile(request):
    """View for user profile."""
    user = request.user
    
    if user.is_landlord:
        landlord = get_object_or_404(Landlord, user=user)
        return render(request, 'accounts/profile.html', {'user': user, 'profile': landlord})
    elif user.is_tenant:
        tenant = get_object_or_404(Tenant, user=user)
        return render(request, 'accounts/profile.html', {'user': user, 'profile': tenant})
    else:
        return render(request, 'accounts/profile.html', {'user': user})


@login_required
def edit_profile(request):
    """View for editing user profile."""
    user = request.user
    
    if request.method == 'POST':
        user_form = UserEditForm(request.POST, request.FILES, instance=user)
        
        if user.is_landlord:
            landlord = get_object_or_404(Landlord, user=user)
            profile_form = LandlordEditForm(request.POST, instance=landlord)
        elif user.is_tenant:
            tenant = get_object_or_404(Tenant, user=user)
            profile_form = TenantEditForm(request.POST, request.FILES, instance=tenant)
        else:
            profile_form = None
        
        if user_form.is_valid() and (profile_form is None or profile_form.is_valid()):
            user_form.save()
            if profile_form:
                profile_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        user_form = UserEditForm(instance=user)
        
        if user.is_landlord:
            landlord = get_object_or_404(Landlord, user=user)
            profile_form = LandlordEditForm(instance=landlord)
        elif user.is_tenant:
            tenant = get_object_or_404(Tenant, user=user)
            profile_form = TenantEditForm(instance=tenant)
        else:
            profile_form = None
    
    return render(request, 'accounts/edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })


@login_required
def dashboard(request):
    """Main dashboard view that redirects to appropriate dashboard based on user type."""
    user = request.user
    
    if user.is_landlord:
        return redirect('landlord_dashboard')
    elif user.is_tenant:
        return redirect('tenant_dashboard')
    else:
        # For admin or other user types
        return render(request, 'accounts/dashboard.html')


@login_required
def landlord_dashboard(request):
    """Dashboard view for landlords."""
    if not request.user.is_landlord:
        messages.error(request, 'Access denied. You are not registered as a landlord.')
        return redirect('dashboard')
    
    landlord = get_object_or_404(Landlord, user=request.user)
    properties = Property.objects.filter(landlord=landlord)
    
    # Get rental agreements for all properties
    rental_agreements = RentalAgreement.objects.filter(property__landlord=landlord)
    
    # Get pending property requests
    property_requests = PropertyRequest.objects.filter(
        property__landlord=landlord,
        status='pending'
    ).order_by('-created_at')
    
    # Get recent payments
    recent_payments = Payment.objects.filter(
        rental_agreement__property__landlord=landlord
    ).order_by('-payment_date')[:5]
    
    # Get unresolved notices
    unresolved_notices = Notice.objects.filter(
        rental_agreement__property__landlord=landlord,
        status__in=['pending', 'in_progress']
    )
    
    context = {
        'landlord': landlord,
        'properties': properties,
        'rental_agreements': rental_agreements,
        'property_requests': property_requests,
        'recent_payments': recent_payments,
        'unresolved_notices': unresolved_notices,
        'properties_count': properties.count(),
        'rented_properties_count': properties.filter(status='rented').count(),
        'available_properties_count': properties.filter(status='available').count(),
        'pending_requests': property_requests.count(),  # Add this line to count pending requests
    }
    
    return render(request, 'accounts/landlord_dashboard.html', context)


@login_required
def tenant_dashboard(request):
    """View for tenant dashboard."""
    if not request.user.is_tenant:
        messages.error(request, 'Access denied. You are not registered as a tenant.')
        return redirect('dashboard')
    
    tenant = get_object_or_404(Tenant, user=request.user)
    
    # Get all rental agreements for the tenant
    rental_agreements = RentalAgreement.objects.filter(tenant=tenant)
    
    # Debug: Print all rental agreements and their statuses
    print(f"Debug - All rental agreements for tenant {tenant.id}:")
    for ra in rental_agreements:
        print(f"- Agreement ID: {ra.id}, Status: {ra.status}, Property: {ra.property.title}")
    
    # Get active rental agreement (case-insensitive match)
    active_agreement = rental_agreements.filter(status__iexact='active').first()
    
    # Get rented properties
    rented_properties = Property.objects.filter(rental_agreements__tenant=tenant, status='rented')
    
    # Get property requests (all statuses to show the tenant their request history)
    property_requests = PropertyRequest.objects.filter(tenant=tenant).order_by('-created_at')
    
    # Get recent payments - Use select_related to improve performance and ensure latest data
    recent_payments = Payment.objects.select_related('rental_agreement', 'rental_agreement__property').filter(
        rental_agreement__tenant=tenant
    ).order_by('-due_date')[:5]  # Order by due date instead of payment date to show most relevant first
    
    # Get upcoming payments - Use select_related and ensure we're getting the latest data
    upcoming_payments = Payment.objects.select_related('rental_agreement', 'rental_agreement__property').filter(
        rental_agreement__tenant=tenant,
        status='pending'
    ).order_by('due_date')[:5]
    
    # Get the next payment due (first upcoming payment)
    next_payment = upcoming_payments.first()
    
    # Get payment details for the active property if exists
    payment_details = None
    if active_agreement and active_agreement.property:
        payment_details = PaymentDetail.objects.filter(property=active_agreement.property).first()
    
    # Get unresolved notices
    unresolved_notices = Notice.objects.filter(
        rental_agreement__tenant=tenant,
        status__in=['pending', 'in_progress']
    )
    
    # Count upcoming payments
    upcoming_payments_count = upcoming_payments.count()
    
    # Count unresolved notices instead of unread notices
    unread_notices_count = Notice.objects.filter(
        rental_agreement__tenant=tenant,
        status__in=['pending', 'in_progress']
    ).count()
    
    context = {
        'tenant': tenant,
        'rental_agreements': rental_agreements,
        'active_agreement': active_agreement,
        'rented_properties': rented_properties,
        'property_requests': property_requests,
        'recent_payments': recent_payments,
        'upcoming_payments': upcoming_payments,
        'upcoming_payments_count': upcoming_payments_count,
        'unresolved_notices': unresolved_notices,
        'unread_notices_count': unread_notices_count,
        'pending_requests_count': property_requests.filter(status='pending').count(),
        'approved_requests_count': property_requests.filter(status='approved').count(),
        'rejected_requests_count': property_requests.filter(status='rejected').count(),
        'next_payment': next_payment,
        'payment_details': payment_details,
    }
    
    return render(request, 'accounts/tenant_dashboard.html', context)
