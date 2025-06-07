from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.core.exceptions import ValidationError
from .models import Payment, Notice, PaymentDetail
from .forms import PaymentForm, NoticeForm, PaymentDetailForm
from properties.models import RentalAgreement, Property
from accounts.models import Landlord, Tenant


@login_required
def payment_list(request):
    """View for listing payments."""
    is_landlord = request.user.is_landlord
    is_tenant = request.user.is_tenant
    
    # Filter payments based on user type
    if is_landlord:
        landlord = get_object_or_404(Landlord, user=request.user)
        payments = Payment.objects.select_related('rental_agreement', 'rental_agreement__property', 'rental_agreement__tenant').filter(
            rental_agreement__property__landlord=landlord
        )
        # Only include properties that have at least one rental agreement
        properties = Property.objects.filter(
            landlord=landlord,
            rental_agreements__isnull=False
        ).distinct()
    elif is_tenant:
        tenant = get_object_or_404(Tenant, user=request.user)
        payments = Payment.objects.select_related('rental_agreement', 'rental_agreement__property').filter(
            rental_agreement__tenant=tenant
        )
        # Only include properties that have active rental agreements for the tenant
        properties = Property.objects.filter(
            rental_agreements__tenant=tenant,
            rental_agreements__isnull=False
        ).distinct()
    else:
        messages.error(request, 'You do not have permission to view payments.')
        return redirect('dashboard')
    
    # Apply filters
    status_filter = request.GET.get('status')
    property_filter = request.GET.get('property')
    month_filter = request.GET.get('month')
    
    if status_filter and status_filter != 'all':
        payments = payments.filter(status=status_filter)
    
    if property_filter and property_filter != 'all':
        payments = payments.filter(rental_agreement__property_id=property_filter)
    
    if month_filter and month_filter != 'all':
        try:
            month, year = month_filter.split('-')
            payments = payments.filter(due_date__month=month, due_date__year=year)
        except ValueError:
            pass
    
    # Order by due date (most recent first)
    payments = payments.order_by('-due_date')
    
    # Get unique months for the filter dropdown
    months = payments.dates('due_date', 'month', order='DESC')
    month_choices = [(d.strftime('%m-%Y'), d.strftime('%B %Y')) for d in months]
    
    context = {
        'payments': payments,
        'properties': properties,
        'is_landlord': is_landlord,
        'is_tenant': is_tenant,
        'status_filter': status_filter or 'all',
        'property_filter': property_filter or 'all',
        'month_filter': month_filter or 'all',
        'month_choices': month_choices,
        'payment_status_choices': Payment.PAYMENT_STATUS_CHOICES,
    }
    
    return render(request, 'payments/payment_list.html', context)


@login_required
def payment_detail(request, payment_id):
    """View for displaying payment details."""
    payment = get_object_or_404(Payment, id=payment_id)
    rental_agreement = payment.rental_agreement
    
    # Check if the user is the landlord of this property or the tenant of this agreement
    is_landlord = request.user.is_landlord and rental_agreement.property.landlord.user == request.user
    is_tenant = request.user.is_tenant and rental_agreement.tenant.user == request.user
    
    if not (is_landlord or is_tenant):
        messages.error(request, 'You do not have permission to view this payment.')
        return redirect('dashboard')
    
    return render(request, 'payments/payment_detail.html', {
        'payment': payment,
        'rental_agreement': rental_agreement,
        'is_landlord': is_landlord,
        'is_tenant': is_tenant
    })


@login_required
def create_payment(request, agreement_id=None):
    """View for creating a new payment."""
    if not request.user.is_landlord:
        messages.error(request, 'Only landlords can create payments.')
        return redirect('payment_list')
    
    landlord = get_object_or_404(Landlord, user=request.user)
    rental_agreement = None
    
    # Handle GET request or invalid form
    if agreement_id:
        rental_agreement = get_object_or_404(RentalAgreement, id=agreement_id)
        
        # Check if the user is the landlord of this property
        if rental_agreement.property.landlord != landlord:
            messages.error(request, 'You do not have permission to create payments for this agreement.')
            return redirect('payment_list')
    
    # Set initial data
    initial_data = {}
    if rental_agreement:
        today = timezone.now().date()
        initial_data = {
            'rental_agreement': rental_agreement.id,
            'amount': rental_agreement.rent_amount,
            'payment_date': today.strftime('%Y-%m-%d'),
            'due_date': today.strftime('%Y-%m-%d'),
            'status': 'paid',
            'payment_method': 'bank_transfer'
        }
    
    if request.method == 'POST':
        # Create a copy of the POST data to modify
        post_data = request.POST.copy()
        
        # Ensure the rental_agreement is set in POST data
        if 'rental_agreement' not in post_data and rental_agreement:
            post_data['rental_agreement'] = rental_agreement.id
            
        form = PaymentForm(post_data, request.FILES, landlord=landlord)
        
        if form.is_valid():
            try:
                payment = form.save(commit=False)
                payment.created_by = request.user
                
                # Ensure required fields are set
                if not payment.payment_date:
                    payment.payment_date = timezone.now().date()
                if not payment.due_date:
                    payment.due_date = timezone.now().date()
                if not payment.status:
                    payment.status = 'paid'
                
                payment.save()
                
                messages.success(
                    request,
                    f'Payment of ${payment.amount} has been successfully recorded for {payment.rental_agreement.property.title}.'
                )
                
                return redirect('property_detail', property_id=payment.rental_agreement.property.id)
                
            except Exception as e:
                messages.error(request, f'Error saving payment: {str(e)}')
        else:
            # Add form errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
                    
            # If form is invalid, re-render with the same data
            return render(request, 'payments/payment_form.html', {
                'form': form,
                'rental_agreement': rental_agreement
            })
    else:
        form = PaymentForm(initial=initial_data, landlord=landlord)
    
    # For GET requests, show the form
    return render(request, 'payments/payment_form.html', {
        'form': form,
        'rental_agreement': rental_agreement
    })


@login_required
def edit_payment(request, payment_id):
    """View for editing a payment."""
    payment = get_object_or_404(Payment, id=payment_id)
    rental_agreement = payment.rental_agreement
    
    # Check if the user is the landlord of this property
    if not request.user.is_landlord or rental_agreement.property.landlord.user != request.user:
        messages.error(request, 'You do not have permission to edit this payment.')
        return redirect('payment_detail', payment_id=payment_id)
    
    # Don't allow editing completed payments
    if payment.status == 'paid':
        messages.error(request, 'Completed payments cannot be edited.')
        return redirect('payment_detail', payment_id=payment_id)
    
    landlord = get_object_or_404(Landlord, user=request.user)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment, landlord=landlord)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payment updated successfully!')
            return redirect('payment_detail', payment_id=payment_id)
    else:
        form = PaymentForm(instance=payment, landlord=landlord)
    
    return render(request, 'payments/edit_payment.html', {
        'form': form,
        'payment': payment
    })


@login_required
def mark_payment_completed(request, payment_id):
    """View for marking a payment as completed."""
    payment = get_object_or_404(Payment, id=payment_id)
    rental_agreement = payment.rental_agreement
    
    # Check if the user is the landlord of this property
    if not request.user.is_landlord or rental_agreement.property.landlord.user != request.user:
        messages.error(request, 'You do not have permission to mark this payment as completed.')
        return redirect('payment_detail', payment_id=payment_id)
    
    # Mark payment as paid and update payment date
    payment.status = 'paid'
    payment.payment_date = timezone.now().date()
    payment.save()
    
    messages.success(request, 'Payment has been successfully marked as paid!')
    
    # Redirect back to the payment detail page
    return redirect('payment_detail', payment_id=payment_id)


@login_required
def tenant_make_payment(request, payment_id):
    """View for tenants to make a payment."""
    payment = get_object_or_404(Payment, id=payment_id)
    rental_agreement = payment.rental_agreement
    
    # Check if the user is the tenant of this agreement
    if not request.user.is_tenant or rental_agreement.tenant.user != request.user:
        messages.error(request, 'You do not have permission to make this payment.')
        return redirect('payment_detail', payment_id=payment_id)
    
    # Don't allow paying already completed payments
    if payment.status == 'paid':
        messages.error(request, 'This payment has already been paid.')
        return redirect('payment_detail', payment_id=payment_id)
    
    # Get payment details for this property if available
    payment_details = PaymentDetail.objects.filter(property=rental_agreement.property).first()
    
    if request.method == 'POST':
        # In a real application, this would integrate with a payment gateway
        # For now, we'll just mark it as paid
        payment.status = 'paid'
        payment.payment_date = timezone.now().date()
        payment.save()
        messages.success(request, 'Payment completed successfully!')
        return redirect('payment_detail', payment_id=payment_id)
    
    return render(request, 'payments/tenant_make_payment.html', {
        'payment': payment,
        'payment_details': payment_details
    })


@login_required
def notice_list(request):
    """View for listing notices."""
    if request.user.is_landlord:
        # Landlords see notices for all their properties
        landlord = get_object_or_404(Landlord, user=request.user)
        notices = Notice.objects.filter(
            rental_agreement__property__landlord=landlord
        ).order_by('-created_at')
    elif request.user.is_tenant:
        # Tenants see only their notices
        tenant = get_object_or_404(Tenant, user=request.user)
        notices = Notice.objects.filter(
            rental_agreement__tenant=tenant
        ).order_by('-created_at')
    else:
        messages.error(request, 'You do not have permission to view notices.')
        return redirect('dashboard')
    
    # Filter by status if specified
    status = request.GET.get('status')
    if status:
        notices = notices.filter(status=status)
    
    return render(request, 'payments/notice_list.html', {
        'notices': notices,
        'status_choices': Notice.NOTICE_STATUS_CHOICES,
    })


@login_required
def notice_detail(request, notice_id):
    """View for displaying notice details."""
    notice = get_object_or_404(Notice, id=notice_id)
    rental_agreement = notice.rental_agreement
    
    # Check if the user is the landlord of this property or the tenant of this agreement
    is_landlord = request.user.is_landlord and rental_agreement.property.landlord.user == request.user
    is_tenant = request.user.is_tenant and rental_agreement.tenant.user == request.user
    
    if not (is_landlord or is_tenant):
        messages.error(request, 'You do not have permission to view this notice.')
        return redirect('dashboard')
    
    return render(request, 'payments/notice_detail.html', {
        'notice': notice,
        'rental_agreement': rental_agreement,
        'is_landlord': is_landlord,
        'is_tenant': is_tenant
    })


@login_required
def select_agreement_for_notice(request):
    """View for selecting a rental agreement before creating a notice."""
    # Both landlords and tenants can create notices
    if not (request.user.is_landlord or request.user.is_tenant):
        messages.error(request, 'You do not have permission to create notices.')
        return redirect('notice_list')
    
    # Get active rental agreements based on user type
    if request.user.is_landlord:
        landlord = get_object_or_404(Landlord, user=request.user)
        rental_agreements = RentalAgreement.objects.filter(
            property__landlord=landlord,
            status='active'
        ).select_related('property', 'tenant', 'tenant__user')
    elif request.user.is_tenant:
        tenant = get_object_or_404(Tenant, user=request.user)
        rental_agreements = RentalAgreement.objects.filter(
            tenant=tenant,
            status='active'
        ).select_related('property', 'property__landlord', 'property__landlord__user')
    
    # If there's only one active agreement, redirect directly to create_notice
    if rental_agreements.count() == 1:
        return redirect('create_notice', agreement_id=rental_agreements.first().id)
    
    return render(request, 'payments/select_agreement_for_notice.html', {
        'rental_agreements': rental_agreements,
        'is_landlord': request.user.is_landlord,
        'is_tenant': request.user.is_tenant
    })


@login_required
def create_notice(request, agreement_id=None):
    """View for creating a new notice."""
    # Both landlords and tenants can create notices
    if not (request.user.is_landlord or request.user.is_tenant):
        messages.error(request, 'You do not have permission to create notices.')
        return redirect('notice_list')
    
    # If agreement_id is provided, pre-select that agreement
    initial_data = {}
    rental_agreement = None
    
    if agreement_id:
        rental_agreement = get_object_or_404(RentalAgreement, id=agreement_id)
        
        # Check if the user is the landlord of this property or the tenant of this agreement
        is_landlord = request.user.is_landlord and rental_agreement.property.landlord.user == request.user
        is_tenant = request.user.is_tenant and rental_agreement.tenant.user == request.user
        
        if not (is_landlord or is_tenant):
            messages.error(request, 'You do not have permission to create notices for this agreement.')
            return redirect('notice_list')
        
        initial_data['rental_agreement'] = rental_agreement
    
    if request.method == 'POST':
        form = NoticeForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            notice = form.save(commit=False)
            notice.created_by = request.user
            
            # Set sender and recipient based on user type
            if request.user.is_landlord:
                notice.sender_landlord = request.user.landlord_profile
                if rental_agreement:
                    notice.recipient_tenant = rental_agreement.tenant
            elif request.user.is_tenant:
                notice.sender_tenant = request.user.tenant_profile
                if rental_agreement:
                    notice.recipient_landlord = rental_agreement.property.landlord
            
            try:
                notice.full_clean()  # This will trigger the model's clean() method
                notice.save()
                messages.success(request, 'Notice created successfully!')
                return redirect('notice_detail', notice_id=notice.id)
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = NoticeForm(initial=initial_data, user=request.user)
    
    return render(request, 'payments/notice_form.html', {
        'form': form,
        'rental_agreement': rental_agreement
    })


@login_required
def edit_notice(request, notice_id):
    """View for editing a notice."""
    notice = get_object_or_404(Notice, id=notice_id)
    rental_agreement = notice.rental_agreement
    
    # Check if the user is the creator of this notice
    if notice.created_by != request.user:
        messages.error(request, 'You do not have permission to edit this notice.')
        return redirect('notice_detail', notice_id=notice_id)
    
    # Don't allow editing resolved notices
    if notice.status == 'resolved':
        messages.error(request, 'Resolved notices cannot be edited.')
        return redirect('notice_detail', notice_id=notice_id)
    
    if request.method == 'POST':
        form = NoticeForm(request.POST, instance=notice, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Notice updated successfully!')
            return redirect('notice_detail', notice_id=notice_id)
    else:
        form = NoticeForm(instance=notice, user=request.user)
    
    return render(request, 'payments/notice_form.html', {
        'form': form,
        'notice': notice
    })


@login_required
def mark_notice_resolved(request, notice_id):
    """View for marking a notice as resolved."""
    notice = get_object_or_404(Notice, id=notice_id)
    rental_agreement = notice.rental_agreement
    
    # Check if the user is the landlord of this property or the tenant of this agreement
    is_landlord = request.user.is_landlord and rental_agreement.property.landlord.user == request.user
    is_tenant = request.user.is_tenant and rental_agreement.tenant.user == request.user
    
    if not (is_landlord or is_tenant):
        messages.error(request, 'You do not have permission to resolve this notice.')
        return redirect('notice_detail', notice_id=notice_id)
    
    if request.method == 'POST':
        notice.status = 'resolved'
        notice.resolved_at = timezone.now()
        notice.resolved_by = request.user
        notice.save()
        messages.success(request, 'Notice marked as resolved successfully!')
        return redirect('notice_detail', notice_id=notice_id)
    
    return render(request, 'payments/mark_notice_resolved.html', {'notice': notice})


@login_required
def tenant_notices(request):
    """View for tenants to see their notices."""
    if not request.user.is_tenant:
        messages.error(request, 'Only tenants can access this page.')
        return redirect('dashboard')
    
    tenant = get_object_or_404(Tenant, user=request.user)
    notices = Notice.objects.filter(
        rental_agreement__tenant=tenant
    ).order_by('-created_at')
    
    return render(request, 'payments/tenant_notices.html', {'notices': notices})


@login_required
def landlord_notices(request):
    """View for landlords to see notices for their properties."""
    if not request.user.is_landlord:
        messages.error(request, 'Only landlords can access this page.')
        return redirect('dashboard')
    
    landlord = get_object_or_404(Landlord, user=request.user)
    notices = Notice.objects.filter(
        rental_agreement__property__landlord=landlord
    ).order_by('-created_at')
    
    return render(request, 'payments/landlord_notices.html', {'notices': notices})


@login_required
def manage_payment_details(request, property_id):
    """View for landlords to manage payment details for a property."""
    property_obj = get_object_or_404(Property, id=property_id)
    
    # Check if the user is the landlord of this property
    if not request.user.is_landlord or property_obj.landlord.user != request.user:
        messages.error(request, 'You do not have permission to manage payment details for this property.')
        return redirect('property_detail', property_id=property_id)
    
    # Get or create payment details for this property
    payment_details, created = PaymentDetail.objects.get_or_create(property=property_obj)
    
    if request.method == 'POST':
        form = PaymentDetailForm(request.POST, request.FILES, instance=payment_details, property_obj=property_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payment details updated successfully!')
            return redirect('property_detail', property_id=property_id)
    else:
        form = PaymentDetailForm(instance=payment_details, property_obj=property_obj)
    
    return render(request, 'payments/manage_payment_details.html', {
        'property': property_obj,
        'payment_details': payment_details,
        'form': form
    })


@login_required
def property_payment_history(request, property_id):
    """View for displaying payment history for a specific property."""
    property_obj = get_object_or_404(Property, id=property_id)
    
    # Check if the user is the landlord of this property or a tenant with an active agreement
    is_landlord = request.user.is_landlord and property_obj.landlord.user == request.user
    is_tenant = False
    
    if request.user.is_tenant:
        tenant = request.user.tenant_profile
        active_agreement = RentalAgreement.objects.filter(
            property=property_obj,
            tenant=tenant,
            status='active'
        ).first()
        if active_agreement:
            is_tenant = True
    
    if not (is_landlord or is_tenant):
        messages.error(request, 'You do not have permission to view payment history for this property.')
        return redirect('dashboard')
    
    # Get all payments for this property
    payments = Payment.objects.filter(
        rental_agreement__property=property_obj
    ).order_by('-due_date')
    
    # Get payment details for this property
    payment_details = PaymentDetail.objects.filter(property=property_obj).first()
    
    return render(request, 'payments/property_payment_history.html', {
        'property': property_obj,
        'payments': payments,
        'payment_details': payment_details,
        'is_landlord': is_landlord,
        'is_tenant': is_tenant
    })
