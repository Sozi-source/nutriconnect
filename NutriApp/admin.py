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
    actions = ['delete_selected_users']  # Custom delete action

    def user_role(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.role
        return 'No profile'
    user_role.short_description = 'Role'

    @admin.action(description="🗑️ Delete selected users (with cascade)")
    def delete_selected_users(self, request, queryset):
        """Custom delete action that handles cascade properly"""
        if not request.user.is_superuser:
            self.message_user(
                request,
                "❌ Only superusers can delete users.",
                level=messages.ERROR
            )
            return

        # Count related objects for display
        total_users = queryset.count()
        related_counts = {}
        
        with transaction.atomic():
            for user in queryset:
                # Count related objects before deletion
                if hasattr(user, 'profile'):
                    related_counts['profiles'] = related_counts.get('profiles', 0) + 1
                if hasattr(user, 'practitioner'):
                    related_counts['practitioners'] = related_counts.get('practitioners', 0) + 1
                
                # Count consultations where user is client
                client_consults = Consultation.objects.filter(client=user).count()
                if client_consults:
                    related_counts['client_consultations'] = related_counts.get('client_consultations', 0) + client_consults
                
                # Count consultations where user is practitioner (via practitioner model)
                if hasattr(user, 'practitioner'):
                    prac_consults = Consultation.objects.filter(practitioner=user.practitioner).count()
                    if prac_consults:
                        related_counts['practitioner_consultations'] = related_counts.get('practitioner_consultations', 0) + prac_consults
                
                # Count reviews
                reviews = Review.objects.filter(reviewer=user).count()
                if reviews:
                    related_counts['reviews'] = related_counts.get('reviews', 0) + reviews
            
            # Perform the deletion
            deleted_count = queryset.delete()
            
            # Show summary message
            summary = f"✅ Successfully deleted {total_users} user(s)."
            if related_counts:
                summary += " Related objects deleted:"
                for key, count in related_counts.items():
                    summary += f" {count} {key},"
                summary = summary.rstrip(',')
            
            self.message_user(request, summary, level=messages.SUCCESS)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.is_superuser:
            # Remove delete action for non-superusers
            if 'delete_selected' in actions:
                del actions['delete_selected']
        return actions

    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete users
        return request.user.is_superuser

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