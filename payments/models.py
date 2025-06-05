from django.db import models
from properties.models import RentalAgreement
from accounts.models import Landlord, Tenant


class Payment(models.Model):
    """Model for rent payments."""
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('other', 'Other'),
    ]
    
    rental_agreement = models.ForeignKey(RentalAgreement, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    due_date = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    receipt = models.FileField(upload_to='documents/', blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payment for {self.rental_agreement.property.title} - {self.payment_date}"
    
    @property
    def is_late(self):
        return self.status != 'completed' and self.due_date < self.payment_date


class Notice(models.Model):
    """Model for notices between landlords and tenants."""
    NOTICE_TYPE_CHOICES = [
        ('maintenance', 'Maintenance Request'),
        ('rent_increase', 'Rent Increase'),
        ('termination', 'Termination Notice'),
        ('inspection', 'Property Inspection'),
        ('general', 'General Notice'),
        ('complaint', 'Complaint'),
    ]
    
    NOTICE_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('cancelled', 'Cancelled'),
    ]
    
    sender_landlord = models.ForeignKey(Landlord, on_delete=models.CASCADE, related_name='sent_notices', null=True, blank=True)
    sender_tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='sent_notices', null=True, blank=True)
    recipient_landlord = models.ForeignKey(Landlord, on_delete=models.CASCADE, related_name='received_notices', null=True, blank=True)
    recipient_tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='received_notices', null=True, blank=True)
    rental_agreement = models.ForeignKey(RentalAgreement, on_delete=models.CASCADE, related_name='notices')
    notice_type = models.CharField(max_length=20, choices=NOTICE_TYPE_CHOICES)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    attachment = models.FileField(upload_to='documents/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=NOTICE_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.notice_type} - {self.subject}"
    
    def clean(self):
        """Ensure that either sender_landlord or sender_tenant is set, but not both."""
        if (self.sender_landlord and self.sender_tenant) or (not self.sender_landlord and not self.sender_tenant):
            raise ValueError("Either sender_landlord or sender_tenant must be set, but not both.")
        
        if (self.recipient_landlord and self.recipient_tenant) or (not self.recipient_landlord and not self.recipient_tenant):
            raise ValueError("Either recipient_landlord or recipient_tenant must be set, but not both.")
