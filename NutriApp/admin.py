from django.contrib import admin
from django.utils.html import format_html
from .models import (
    User, UserProfile, Practitioner, Specialty, 
    Availability, Consultation, Review
)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_active', 'is_staff']
    list_filter = ['is_active', 'is_staff']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['email']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone']
    list_filter = ['role']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'phone']

@admin.register(Practitioner)
class PractitionerAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'city', 'hourly_rate', 'currency', 
        'years_of_experience', 'is_verified', 'profile_complete'
    ]
    list_filter = ['is_verified', 'profile_complete', 'city', 'currency']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'city']
    filter_horizontal = ['specialties']  # Better UI for ManyToMany field
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'is_verified', 'profile_complete')
        }),
        ('Professional Details', {
            'fields': ('bio', 'specialties', 'city', 'years_of_experience')
        }),
        ('Rate Information', {
            'fields': ('hourly_rate', 'currency')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'practitioner_count']
    search_fields = ['name']
    
    def practitioner_count(self, obj):
        """Count practitioners with this specialty"""
        count = obj.practitioner.count()  # FIXED: Changed from practitioner_set to practitioner
        return count
    practitioner_count.short_description = 'Practitioners'

@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = [
        'practitioner', 'recurrence_type', 'day_of_week', 
        'specific_date', 'start_time', 'end_time', 'is_available'
    ]
    list_filter = ['recurrence_type', 'is_available', 'day_of_week']
    search_fields = ['practitioner__user__email', 'notes']
    date_hierarchy = 'specific_date'

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = [
        'client', 'practitioner', 'date', 'time', 
        'status', 'duration_minutes'
    ]
    list_filter = ['status', 'date']
    search_fields = ['client__email', 'practitioner__user__email']
    date_hierarchy = 'date'
    readonly_fields = ['version']
    
    fieldsets = (
        ('Participants', {
            'fields': ('client', 'practitioner')
        }),
        ('Appointment Details', {
            'fields': ('date', 'time', 'duration_minutes', 'status')
        }),
        ('Notes', {
            'fields': ('client_notes', 'practitioner_notes')
        }),
        ('System', {
            'fields': ('version',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['consultation', 'reviewer', 'rating', 'created_at']
    list_filter = ['rating']
    search_fields = ['reviewer__email', 'comment']
    date_hierarchy = 'created_at'