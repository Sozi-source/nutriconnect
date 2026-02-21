from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django.db import transaction
from .models import (
    User, UserProfile, Practitioner, Specialty,
    Availability, Consultation, Review
)

# ==================== ADMIN ACTIONS ====================

@admin.action(description="✅ Approve selected practitioners")
def approve_practitioners(modeladmin, request, queryset):
    approved = queryset.update(is_verified=True)
    modeladmin.message_user(
        request,
        f"✅ Approved {approved} practitioners.",
        level=messages.SUCCESS
    )

@admin.action(description="❌ Reject selected practitioners")
def reject_practitioners(modeladmin, request, queryset):
    rejected = queryset.update(is_verified=False)
    modeladmin.message_user(
        request,
        f"❌ Rejected {rejected} practitioners.",
        level=messages.WARNING
    )

# ==================== USER ADMIN ====================

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_active', 'is_staff', 'user_role']
    list_filter = ['is_active', 'is_staff']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['email']

    def user_role(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.role
        return 'No profile'
    user_role.short_description = 'Role'

# ==================== USER PROFILE ADMIN ====================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone']
    list_filter = ['role']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'phone']

# ==================== PRACTITIONER ADMIN ====================

@admin.register(Practitioner)
class PractitionerAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'city', 'hourly_rate', 'currency',
        'years_of_experience', 'verification_status', 'profile_complete'
    ]
    list_filter = ['is_verified', 'profile_complete', 'city', 'currency']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'city']
    filter_horizontal = ['specialties']
    readonly_fields = ['created_at', 'updated_at']
    actions = [approve_practitioners, reject_practitioners]

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

    def verification_status(self, obj):
        if obj.is_verified:
            return format_html(
                '<span style="color: white; background-color: #27ae60; padding: 3px 8px; border-radius: 4px;">✅ Verified</span>'
            )
        else:
            return format_html(
                '<span style="color: white; background-color: #f39c12; padding: 3px 8px; border-radius: 4px;">⏳ Pending</span>'
            )
    verification_status.short_description = 'Status'

# ==================== SPECIALTY ADMIN ====================

@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'practitioner_count']
    search_fields = ['name']

    def practitioner_count(self, obj):
        return obj.practitioner.count()
    practitioner_count.short_description = 'Practitioners'

# ==================== AVAILABILITY ADMIN ====================

@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = [
        'practitioner', 'recurrence_type', 'day_of_week',
        'specific_date', 'start_time', 'end_time', 'is_available'
    ]
    list_filter = ['recurrence_type', 'is_available', 'day_of_week']
    search_fields = ['practitioner__user__email', 'notes']
    date_hierarchy = 'specific_date'

# ==================== CONSULTATION ADMIN ====================

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

# ==================== REVIEW ADMIN ====================

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['consultation', 'reviewer', 'rating', 'created_at']
    list_filter = ['rating']
    search_fields = ['reviewer__email', 'comment']
    date_hierarchy = 'created_at'
