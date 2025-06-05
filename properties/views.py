from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponseForbidden
from django.forms import modelformset_factory
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from .models import Property, PropertyImage, RentalAgreement, PropertyRequest
from .forms import PropertyForm, PropertyImageForm, RentalAgreementForm, PropertyRequestForm
from accounts.models import Landlord, Tenant


def property_list(request):
    """View for listing all available properties."""
    properties = Property.objects.filter(status='available')
    
    # Filter by property type if specified
    property_type = request.GET.get('property_type')
    if property_type:
        properties = properties.filter(property_type=property_type)
    
    # Filter by price range if specified
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        properties = properties.filter(rent_amount__gte=min_price)
    if max_price:
        properties = properties.filter(rent_amount__lte=max_price)
    
    # Filter by bedrooms if specified
    bedrooms = request.GET.get('bedrooms')
    if bedrooms:
        properties = properties.filter(bedrooms=bedrooms)
    
    # Filter by city if specified
    city = request.GET.get('city')
    if city:
        properties = properties.filter(city__icontains=city)
    
    return render(request, 'properties/property_list.html', {
        'properties': properties,
        'property_types': Property.PROPERTY_TYPE_CHOICES,
    })


def property_detail(request, property_id):
    """View for displaying property details."""
    property_obj = get_object_or_404(Property, id=property_id)
    images = property_obj.images.all()
    
    # Check if the user is a tenant and has already requested this property
    user_has_requested = False
    if request.user.is_authenticated and hasattr(request.user, 'tenant_profile'):
        tenant = request.user.tenant_profile
        user_has_requested = PropertyRequest.objects.filter(
            property=property_obj,
            tenant=tenant,
            status__in=['pending', 'approved']
        ).exists()
    
    return render(request, 'properties/property_detail.html', {
        'property': property_obj,
        'images': images,
        'user_has_requested': user_has_requested,
    })


@login_required
def create_property(request):
    """View for creating a new property."""
    if not request.user.is_landlord:
        messages.error(request, 'Only landlords can create properties.')
        return redirect('property_list')
    
    landlord = get_object_or_404(Landlord, user=request.user)
    
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        if form.is_valid():
            property_obj = form.save(commit=False)
            property_obj.landlord = landlord
            property_obj.save()
            messages.success(request, 'Property created successfully!')
            return redirect('add_property_images', property_id=property_obj.id)
    else:
        form = PropertyForm()
    
    return render(request, 'properties/create_property.html', {'form': form})


@login_required
def edit_property(request, property_id):
    """View for editing an existing property."""
    property_obj = get_object_or_404(Property, id=property_id)
    
    # Check if the user is the landlord of this property
    if not request.user.is_landlord or property_obj.landlord.user != request.user:
        messages.error(request, 'You do not have permission to edit this property.')
        return redirect('property_detail', property_id=property_id)
    
    if request.method == 'POST':
        form = PropertyForm(request.POST, instance=property_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Property updated successfully!')
            return redirect('property_detail', property_id=property_id)
    else:
        form = PropertyForm(instance=property_obj)
    
    return render(request, 'properties/edit_property.html', {
        'form': form,
        'property': property_obj
    })


@login_required
def delete_property(request, property_id):
    """View for deleting a property."""
    property_obj = get_object_or_404(Property, id=property_id)
    
    # Check if the user is the landlord of this property
    if not request.user.is_landlord or property_obj.landlord.user != request.user:
        messages.error(request, 'You do not have permission to delete this property.')
        return redirect('property_detail', property_id=property_id)
    
    if request.method == 'POST':
        property_obj.delete()
        messages.success(request, 'Property deleted successfully!')
        return redirect('landlord_dashboard')
    
    return render(request, 'properties/delete_property.html', {'property': property_obj})


@login_required
def add_property_images(request, property_id):
    """View for adding images to a property."""
    property_obj = get_object_or_404(Property, id=property_id)
    
    # Check if the user is the landlord of this property
    if not request.user.is_landlord or property_obj.landlord.user != request.user:
        messages.error(request, 'You do not have permission to add images to this property.')
        return redirect('property_detail', property_id=property_id)
    
    ImageFormSet = modelformset_factory(PropertyImage, form=PropertyImageForm, extra=5, max_num=10)
    
    if request.method == 'POST':
        formset = ImageFormSet(request.POST, request.FILES, queryset=PropertyImage.objects.none())
        if formset.is_valid():
            for form in formset.cleaned_data:
                if form:
                    image = form['image']
                    caption = form.get('caption', '')
                    is_primary = form.get('is_primary', False)
                    
                    # If this is marked as primary, unmark all others
                    if is_primary:
                        PropertyImage.objects.filter(property=property_obj, is_primary=True).update(is_primary=False)
                    
                    PropertyImage.objects.create(
                        property=property_obj,
                        image=image,
                        caption=caption,
                        is_primary=is_primary
                    )
            
            messages.success(request, 'Images added successfully!')
            return redirect('property_detail', property_id=property_id)
    else:
        formset = ImageFormSet(queryset=PropertyImage.objects.none())
    
    return render(request, 'properties/add_property_images.html', {
        'formset': formset,
        'property': property_obj
    })


@login_required
def delete_property_image(request, image_id):
    """View for deleting a property image."""
    image = get_object_or_404(PropertyImage, id=image_id)
    property_obj = image.property
    
    # Check if the user is the landlord of this property
    if not request.user.is_landlord or property_obj.landlord.user != request.user:
        messages.error(request, 'You do not have permission to delete this image.')
        return redirect('property_detail', property_id=property_obj.id)
    
    if request.method == 'POST':
        # If this was the primary image, set another image as primary if available
        if image.is_primary:
            other_image = PropertyImage.objects.filter(property=property_obj).exclude(id=image_id).first()
            if other_image:
                other_image.is_primary = True
                other_image.save()
        
        image.delete()
        messages.success(request, 'Image deleted successfully!')
        return redirect('property_detail', property_id=property_obj.id)
    
    return render(request, 'properties/delete_property_image.html', {
        'image': image,
        'property': property_obj
    })


@login_required
def set_primary_image(request, image_id):
    """View for setting a property image as primary."""
    image = get_object_or_404(PropertyImage, id=image_id)
    property_obj = image.property
    
    # Check if the user is the landlord of this property
    if not request.user.is_landlord or property_obj.landlord.user != request.user:
        return HttpResponseForbidden('You do not have permission to modify this image.')
    
    # Unset all other primary images for this property
    PropertyImage.objects.filter(property=property_obj, is_primary=True).update(is_primary=False)
    
    # Set this image as primary
    image.is_primary = True
    image.save()
    
    if request.is_ajax():
        return JsonResponse({'success': True})
    else:
        messages.success(request, 'Primary image updated successfully!')
        return redirect('property_detail', property_id=property_obj.id)


@login_required
def property_agreements(request, property_id):
    """View for listing all rental agreements for a property."""
    property_obj = get_object_or_404(Property, id=property_id)
    
    # Check if the user is the landlord of this property
    if not request.user.is_landlord or property_obj.landlord.user != request.user:
        messages.error(request, 'You do not have permission to view agreements for this property.')
        return redirect('property_detail', property_id=property_id)
    
    agreements = RentalAgreement.objects.filter(property=property_obj)
    
    return render(request, 'properties/property_agreements.html', {
        'property': property_obj,
        'agreements': agreements
    })


@login_required
def agreement_detail(request, agreement_id):
    """View for displaying rental agreement details."""
    agreement = get_object_or_404(RentalAgreement, id=agreement_id)
    property_obj = agreement.property
    
    # Check if the user is the landlord of this property or the tenant of this agreement
    is_landlord = request.user.is_landlord and property_obj.landlord.user == request.user
    is_tenant = request.user.is_tenant and agreement.tenant.user == request.user
    
    if not (is_landlord or is_tenant):
        messages.error(request, 'You do not have permission to view this agreement.')
        return redirect('dashboard')
    
    return render(request, 'properties/agreement_detail.html', {
        'agreement': agreement,
        'property': property_obj,
        'is_landlord': is_landlord,
        'is_tenant': is_tenant
    })


@login_required
def edit_agreement(request, agreement_id):
    """View for editing a rental agreement."""
    agreement = get_object_or_404(RentalAgreement, id=agreement_id)
    property_obj = agreement.property
    
    # Check if the user is the landlord of this property
    if not request.user.is_landlord or property_obj.landlord.user != request.user:
        messages.error(request, 'You do not have permission to edit this agreement.')
        return redirect('agreement_detail', agreement_id=agreement_id)
    
    if request.method == 'POST':
        form = RentalAgreementForm(request.POST, request.FILES, instance=agreement)
        if form.is_valid():
            form.save()
            messages.success(request, 'Agreement updated successfully!')
            return redirect('agreement_detail', agreement_id=agreement_id)
    else:
        form = RentalAgreementForm(instance=agreement)
    
    return render(request, 'properties/edit_agreement.html', {
        'form': form,
        'agreement': agreement,
        'property': property_obj
    })


@login_required
def terminate_agreement(request, agreement_id):
    """View for terminating a rental agreement."""
    agreement = get_object_or_404(RentalAgreement, id=agreement_id)
    property_obj = agreement.property
    
    # Check if the user is the landlord of this property
    if not request.user.is_landlord or property_obj.landlord.user != request.user:
        messages.error(request, 'You do not have permission to terminate this agreement.')
        return redirect('agreement_detail', agreement_id=agreement_id)
    
    if request.method == 'POST':
        agreement.status = 'terminated'
        agreement.save()
        
        # Update property status to available
        property_obj.status = 'available'
        property_obj.save()
        
        messages.success(request, 'Agreement terminated successfully!')
        return redirect('property_agreements', property_id=property_obj.id)
    
    return render(request, 'properties/terminate_agreement.html', {
        'agreement': agreement,
        'property': property_obj
    })


@login_required
def request_property(request, property_id):
    """View for tenants to request a property."""
    property_obj = get_object_or_404(Property, id=property_id)
    
    # Check if the property is available
    if property_obj.status != 'available':
        messages.error(request, 'This property is not available for rent.')
        return redirect('property_detail', property_id=property_id)
    
    # Check if the user is a tenant
    if not request.user.is_tenant:
        messages.error(request, 'Only tenants can request properties.')
        return redirect('property_detail', property_id=property_id)
    
    tenant = get_object_or_404(Tenant, user=request.user)
    
    # Check if the tenant has already requested this property
    existing_request = PropertyRequest.objects.filter(
        property=property_obj,
        tenant=tenant,
        status__in=['pending', 'approved']
    ).first()
    
    if existing_request:
        messages.info(request, 'You have already requested this property.')
        return redirect('property_detail', property_id=property_id)
    
    if request.method == 'POST':
        form = PropertyRequestForm(request.POST)
        if form.is_valid():
            property_request = form.save(commit=False)
            property_request.property = property_obj
            property_request.tenant = tenant
            property_request.save()
            messages.success(request, 'Property request submitted successfully!')
            return redirect('property_detail', property_id=property_id)
    else:
        form = PropertyRequestForm()
    
    return render(request, 'properties/request_property.html', {
        'form': form,
        'property': property_obj
    })


@login_required
def property_requests(request):
    """View for landlords to see property requests or tenants to see their own requests."""
    if request.user.is_landlord:
        landlord = get_object_or_404(Landlord, user=request.user)
        
        # Get all pending requests for properties owned by this landlord
        requests = PropertyRequest.objects.filter(
            property__landlord=landlord,
            status='pending'
        ).order_by('-created_at')
    elif request.user.is_tenant:
        tenant = get_object_or_404(Tenant, user=request.user)
        
        # Get all requests made by this tenant (all statuses)
        requests = PropertyRequest.objects.filter(
            tenant=tenant
        ).order_by('-created_at')
    else:
        messages.error(request, 'You must be a landlord or tenant to view property requests.')
        return redirect('dashboard')
    
    # Pagination
    paginator = Paginator(requests, 10)  # Show 10 requests per page
    page = request.GET.get('page')
    try:
        requests = paginator.page(page)
    except PageNotAnInteger:
        requests = paginator.page(1)
    except EmptyPage:
        requests = paginator.page(paginator.num_pages)
    
    return render(request, 'properties/property_request_list.html', {'requests': requests})


@login_required
def request_detail(request, request_id):
    """View for displaying property request details."""
    property_request = get_object_or_404(PropertyRequest, id=request_id)
    property_obj = property_request.property
    
    # Check if the user is the landlord of this property or the tenant who made the request
    is_landlord = request.user.is_landlord and property_obj.landlord.user == request.user
    is_tenant = request.user.is_tenant and property_request.tenant.user == request.user
    
    if not (is_landlord or is_tenant):
        messages.error(request, 'You do not have permission to view this request.')
        return redirect('dashboard')
    
    return render(request, 'properties/property_request_detail.html', {
        'property_request': property_request,
        'property': property_obj,
        'is_landlord': is_landlord,
        'is_tenant': is_tenant
    })


@login_required
def approve_request(request, request_id):
    """View for landlords to approve a property request."""
    property_request = get_object_or_404(PropertyRequest, id=request_id)
    property_obj = property_request.property
    
    # Check if the user is the landlord of this property
    if not request.user.is_landlord or property_obj.landlord.user != request.user:
        messages.error(request, 'You do not have permission to approve this request.')
        return redirect('request_detail', request_id=request_id)
    
    # Check if the property is still available
    if property_obj.status != 'available':
        messages.error(request, 'This property is no longer available for rent.')
        return redirect('request_detail', request_id=request_id)
    
    if request.method == 'POST':
        # Update request status
        property_request.status = 'approved'
        property_request.save()
        
        # Create rental agreement
        agreement = RentalAgreement(
            property=property_obj,
            tenant=property_request.tenant,
            start_date=property_request.requested_move_in_date,
            end_date=property_request.requested_move_in_date.replace(year=property_request.requested_move_in_date.year + 1),
            rent_amount=property_obj.rent_amount,
            security_deposit=property_obj.security_deposit,
            status='pending',
            terms_and_conditions='Standard rental agreement terms and conditions apply.'
        )
        agreement.save()
        
        # Update property status
        property_obj.status = 'rented'
        property_obj.save()
        
        # Reject all other pending requests for this property
        PropertyRequest.objects.filter(
            property=property_obj,
            status='pending'
        ).exclude(id=request_id).update(status='rejected')
        
        messages.success(request, 'Request approved and rental agreement created successfully!')
        return redirect('agreement_detail', agreement_id=agreement.id)
    
    return render(request, 'properties/approve_request.html', {
        'request': property_request,
        'property': property_obj
    })


@login_required
def reject_request(request, request_id):
    """View for landlords to reject a property request."""
    property_request = get_object_or_404(PropertyRequest, id=request_id)
    property_obj = property_request.property
    
    # Check if the user is the landlord of this property
    if not request.user.is_landlord or property_obj.landlord.user != request.user:
        messages.error(request, 'You do not have permission to reject this request.')
        return redirect('request_detail', request_id=request_id)
    
    if request.method == 'POST':
        property_request.status = 'rejected'
        property_request.save()
        messages.success(request, 'Request rejected successfully!')
        return redirect('property_requests')
    
    return render(request, 'properties/reject_request.html', {
        'request': property_request,
        'property': property_obj
    })
