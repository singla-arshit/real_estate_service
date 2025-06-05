from django.contrib import admin
from .models import Payment, Notice

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('rental_agreement', 'amount', 'status', 'due_date', 'payment_date')
    list_filter = ('status', 'payment_method', 'rental_agreement__property__property_type')
    search_fields = (
        'rental_agreement__property__title',
        'rental_agreement__tenant__user__username',
        'rental_agreement__tenant__user__email'
    )
    ordering = ('-due_date',)
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('rental_agreement',)

    fieldsets = (
        (None, {
            'fields': ('rental_agreement', 'status')
        }),
        ('Payment Details', {
            'fields': ('amount', 'due_date', 'payment_date', 'payment_method', 'transaction_id')
        }),
        ('Notes & Audit', {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Prefetch related data to optimize queries
        return qs.select_related('rental_agreement__property', 'rental_agreement__tenant__user')

@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ('rental_agreement', 'subject', 'notice_type', 'status', 'created_at')
    list_filter = ('status', 'notice_type', 'rental_agreement__property__property_type')
    search_fields = (
        'subject',
        'message',
        'rental_agreement__property__title',
        'rental_agreement__tenant__user__username'
    )
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('rental_agreement',)

    fieldsets = (
        (None, {
            'fields': ('rental_agreement', 'subject', 'notice_type', 'status')
        }),
        ('Content', {
            'fields': ('message',)
        }),
        ('Audit & Resolution', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Prefetch related data to optimize queries
        return qs.select_related('rental_agreement__property', 'rental_agreement__tenant__user')
