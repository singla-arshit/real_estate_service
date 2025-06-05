from django.contrib import admin
from .models import Property, PropertyImage, RentalAgreement, PropertyRequest

class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1 # Number of empty forms to display
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return obj.image.url
        return "(No image)"
    image_preview.short_description = 'Image Preview'

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'landlord', 'property_type', 'status', 'rent_amount', 'city', 'created_at')
    list_filter = ('property_type', 'status', 'city', 'state')
    search_fields = ('title', 'description', 'address', 'city', 'landlord__user__username')
    ordering = ('-created_at',)
    inlines = [PropertyImageInline]
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('title', 'landlord', 'description', 'property_type', 'status')
        }),
        ('Location', {
            'fields': ('address', 'city', 'state', 'zip_code')
        }),
        ('Details', {
            'fields': ('bedrooms', 'bathrooms', 'area_sqft', 'amenities')
        }),
        ('Pricing & Availability', {
            'fields': ('rent_amount', 'security_deposit', 'available_from')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('property', 'caption', 'is_primary', 'image_preview')
    list_filter = ('is_primary', 'property__property_type')
    search_fields = ('property__title', 'caption')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return obj.image.url
        return "(No image)"
    image_preview.short_description = 'Image Preview'

@admin.register(RentalAgreement)
class RentalAgreementAdmin(admin.ModelAdmin):
    list_display = ('property', 'tenant', 'status', 'start_date', 'end_date', 'rent_amount')
    list_filter = ('status', 'property__property_type')
    search_fields = ('property__title', 'tenant__user__username', 'tenant__user__email')
    ordering = ('-start_date',)
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('property', 'tenant') # For easier selection with many properties/tenants

    fieldsets = (
        (None, {
            'fields': ('property', 'tenant', 'status')
        }),
        ('Agreement Details', {
            'fields': ('start_date', 'end_date', 'rent_amount', 'security_deposit')
        }),
        ('Documents & Terms', {
            'fields': ('terms_and_conditions', 'agreement_document')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(PropertyRequest)
class PropertyRequestAdmin(admin.ModelAdmin):
    list_display = ('property', 'tenant', 'status', 'requested_move_in_date', 'created_at')
    list_filter = ('status', 'property__property_type')
    search_fields = ('property__title', 'tenant__user__username', 'message')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('property', 'tenant')

    fieldsets = (
        (None, {
            'fields': ('property', 'tenant', 'status')
        }),
        ('Request Details', {
            'fields': ('requested_move_in_date', 'message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
