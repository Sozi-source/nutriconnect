from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html
from .models import Practitioner, User, Specialty, Consultation, Availability, Review

class PractitionerAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialty_list', 'city', 'hourly_rate', 'verification_badge', 'created_at']
    list_filter = ['is_verified', 'specialties', 'city']
    search_fields = ['user__username', 'user__email', 'bio', 'city']
    readonly_fields = ['created_at', 'updated_at']
    
    def specialty_list(self, obj):
        return ", ".join([s.name for s in obj.specialties.all()])
    specialty_list.short_description = 'Specialties'
    
    def verification_badge(self, obj):
        if obj.is_verified:
            return format_html('<span style="background: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">✓ Verified</span>')
        return format_html('<span style="background: #ffc107; color: black; padding: 3px 10px; border-radius: 3px;">⏳ Pending</span>')
    verification_badge.short_description = 'Status'
    
    actions = ['approve_practitioners', 'reject_practitioners']
    
    def approve_practitioners(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} practitioner(s) approved successfully.')
    approve_practitioners.short_description = "Approve selected practitioners"
    
    def reject_practitioners(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'{updated} practitioner(s) rejected.')
    reject_practitioners.short_description = "Reject selected practitioners"
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'bio')
        }),
        ('Professional Details', {
            'fields': ('specialties', 'years_of_experience', 'is_verified')
        }),
        ('Location & Rates', {
            'fields': ('city', 'hourly_rate', 'currency')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']

class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

class ConsultationAdmin(admin.ModelAdmin):
    list_display = ['id', 'client', 'practitioner', 'scheduled_time', 'status']
    list_filter = ['status', 'scheduled_time']
    search_fields = ['client__username', 'practitioner__user__username']

class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ['practitioner', 'day_of_week', 'start_time', 'end_time', 'is_available']
    list_filter = ['day_of_week', 'is_available']

class ReviewAdmin(admin.ModelAdmin):
    list_display = ['consultation', 'reviewer', 'rating', 'created_at']
    list_filter = ['rating']

# Register your models
admin.site.register(Practitioner, PractitionerAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Specialty, SpecialtyAdmin)
admin.site.register(Consultation, ConsultationAdmin)
admin.site.register(Availability, AvailabilityAdmin)
admin.site.register(Review, ReviewAdmin)

# Customize admin site header
admin.site.site_header = "NutriConnect Administration"
admin.site.site_title = "NutriConnect Admin"
admin.site.index_title = "Welcome to NutriConnect Admin Portal"