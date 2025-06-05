from django.db import models
from django.utils import timezone
from accounts.models import Landlord, Tenant


class Property(models.Model):
    """Model for real estate properties."""
    PROPERTY_STATUS_CHOICES = [
        ('available', 'Available'),
        ('rented', 'Rented'),
        ('maintenance', 'Under Maintenance'),
        ('not_available', 'Not Available'),
    ]
    
    PROPERTY_TYPE_CHOICES = [
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('condo', 'Condominium'),
        ('commercial', 'Commercial Space'),
        ('land', 'Land'),
        ('other', 'Other'),
    ]
    
    landlord = models.ForeignKey(Landlord, on_delete=models.CASCADE, related_name='properties')
    title = models.CharField(max_length=200)
    description = models.TextField()
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES, default='apartment')
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)
    bedrooms = models.PositiveIntegerField(default=1)
    bathrooms = models.DecimalField(max_digits=3, decimal_places=1, default=1.0)
    area_sqft = models.PositiveIntegerField()
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2)
    available_from = models.DateField()
    status = models.CharField(max_length=20, choices=PROPERTY_STATUS_CHOICES, default='available')
    amenities = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name_plural = "Properties"


class PropertyImage(models.Model):
    """Model for property images."""
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='property_images/')
    is_primary = models.BooleanField(default=False)
    caption = models.CharField(max_length=200, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.property.title}"


class RentalAgreement(models.Model):
    """Model for rental agreements between landlords and tenants."""
    AGREEMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
    ]
    
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='rental_agreements')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='rental_agreements')
    start_date = models.DateField()
    end_date = models.DateField()
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2)
    agreement_document = models.FileField(upload_to='documents/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=AGREEMENT_STATUS_CHOICES, default='pending')
    terms_and_conditions = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Agreement for {self.property.title} - {self.tenant.user.email}"
    
    def is_active(self):
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date and self.status == 'active'


class PropertyRequest(models.Model):
    """Model for property rental requests from tenants."""
    REQUEST_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='requests')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='property_requests')
    message = models.TextField()
    requested_move_in_date = models.DateField()
    status = models.CharField(max_length=20, choices=REQUEST_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Request for {self.property.title} by {self.tenant.user.email}"
