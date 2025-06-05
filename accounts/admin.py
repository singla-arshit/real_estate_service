from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Landlord, Tenant

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff', 'is_landlord', 'is_tenant')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'is_landlord', 'is_tenant')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone_number', 'profile_picture')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('User Type', {'fields': ('is_landlord', 'is_tenant')}),
        ('Timestamps', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone_number', 'profile_picture', 'is_landlord', 'is_tenant'),
        }),
    )

class LandlordAdmin(admin.ModelAdmin):
    list_display = ('user', 'company_name', 'get_properties_count')
    search_fields = ('user__username', 'user__email', 'company_name')

    def get_properties_count(self, obj):
        return obj.properties.count()
    get_properties_count.short_description = 'Properties Count'

class TenantAdmin(admin.ModelAdmin):
    list_display = ('user', 'employment_status', 'get_active_agreements_count')
    search_fields = ('user__username', 'user__email', 'employment_status')

    def get_active_agreements_count(self, obj):
        return obj.rental_agreements.filter(status='active').count()
    get_active_agreements_count.short_description = 'Active Agreements'

admin.site.register(User, CustomUserAdmin)
admin.site.register(Landlord, LandlordAdmin)
admin.site.register(Tenant, TenantAdmin)
