from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, UserProfile, Practitioner, Specialty,
    Availability, Consultation, Review, PractitionerApplication
)
from django.utils import timezone
# ==================== ADMIN ACTIONS ====================

@admin.action(description="✅ Approve selected practitioners")
def approve_practitioners(modeladmin, request, queryset):
    count = queryset.update(is_verified=True)
    modeladmin.message_user(
        request,
        f"✅ Approved {count} practitioner(s).",
        level=messages.SUCCESS
    )

@admin.action(description="❌ Reject selected practitioners")
def reject_practitioners(modeladmin, request, queryset):
    count = queryset.update(is_verified=False)
    modeladmin.message_user(
        request,
        f"❌ Rejected {count} practitioner(s).",
        level=messages.WARNING
    )

@admin.action(description="✅ Approve selected applications")
def approve_applications(modeladmin, request, queryset):
    with transaction.atomic():
        for application in queryset:
            application.approve(request.user)
    modeladmin.message_user(
        request,
        f"✅ Approved {queryset.count()} application(s).",
        level=messages.SUCCESS
    )

@admin.action(description="❌ Reject selected applications")
def reject_applications(modeladmin, request, queryset):
    reason = request.POST.get('rejection_reason', 'Not specified')
    with transaction.atomic():
        for application in queryset:
            application.reject(request.user, reason)
    modeladmin.message_user(
        request,
        f"❌ Rejected {queryset.count()} application(s).",
        level=messages.WARNING
    )

# ==================== USER ADMIN ====================

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_active', 'is_staff', 'user_role', 'user_actions']
    list_filter = ['is_active', 'is_staff', 'profile__role']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['email']
    actions = ['delete_selected_users']
    
    # Remove username field
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

    def user_role(self, obj):
        if hasattr(obj, 'profile'):
            colors = {
                'client': '#3498db',
                'practitioner': '#27ae60',
            }
            color = colors.get(obj.profile.role, '#95a5a6')
            return format_html(
                '<span style="color: white; background-color: {}; padding: 3px 8px; border-radius: 4px;">{}</span>',
                color, obj.profile.role.title()
            )
        return format_html(
            '<span style="color: white; background-color: #95a5a6; padding: 3px 8px; border-radius: 4px;">No Profile</span>'
        )
    user_role.short_description = 'Role'

    def user_actions(self, obj):
        buttons = []
        if obj.is_active:
            buttons.append(
                f'<a class="button" href="/admin/NutriApp/user/{obj.id}/deactivate/" '
                f'onclick="return confirm(\'Deactivate {obj.email}?\')" '
                f'style="background-color: #e74c3c; color: white; padding: 3px 8px; '
                f'border-radius: 4px; text-decoration: none; margin-right: 5px;">Deactivate</a>'
            )
        else:
            buttons.append(
                f'<a class="button" href="/admin/NutriApp/user/{obj.id}/activate/" '
                f'style="background-color: #27ae60; color: white; padding: 3px 8px; '
                f'border-radius: 4px; text-decoration: none; margin-right: 5px;">Activate</a>'
            )
        
        if hasattr(obj, 'practitioner') and not obj.practitioner.is_verified:
            buttons.append(
                f'<a class="button" href="/admin/NutriApp/user/{obj.id}/verify/" '
                f'style="background-color: #f39c12; color: white; padding: 3px 8px; '
                f'border-radius: 4px; text-decoration: none;">Verify</a>'
            )
        
        return format_html(''.join(buttons))
    user_actions.short_description = 'Actions'

    @admin.action(description="🗑️ Delete selected users (with all related data)")
    def delete_selected_users(self, request, queryset):
        if not request.user.is_superuser:
            self.message_user(
                request,
                "❌ Only superusers can delete users.",
                level=messages.ERROR
            )
            return

        total_users = queryset.count()
        deleted_summary = {
            'users': 0,
            'profiles': 0,
            'practitioners': 0,
            'consultations': 0,
            'availabilities': 0,
            'reviews': 0,
            'applications': 0
        }

        with transaction.atomic():
            for user in queryset:
                # Count related objects
                if hasattr(user, 'profile'):
                    deleted_summary['profiles'] += 1
                
                if hasattr(user, 'practitioner'):
                    practitioner = user.practitioner
                    # Count consultations for this practitioner
                    consults = Consultation.objects.filter(practitioner=practitioner).count()
                    deleted_summary['consultations'] += consults
                    # Count availability
                    avail = Availability.objects.filter(practitioner=practitioner).count()
                    deleted_summary['availabilities'] += avail
                    # Count applications
                    if hasattr(practitioner, 'application'):
                        deleted_summary['applications'] += 1
                    deleted_summary['practitioners'] += 1
                
                # Count consultations where user is client
                client_consults = Consultation.objects.filter(client=user).count()
                deleted_summary['consultations'] += client_consults
                
                # Count reviews
                reviews = Review.objects.filter(reviewer=user).count()
                deleted_summary['reviews'] += reviews
                
                # Delete the user (cascade will handle related objects)
                user.delete()
                deleted_summary['users'] += 1

            # Create success message
            message = f"✅ Successfully deleted {deleted_summary['users']} user(s)."
            if deleted_summary['profiles']:
                message += f" {deleted_summary['profiles']} profile(s),"
            if deleted_summary['practitioners']:
                message += f" {deleted_summary['practitioners']} practitioner(s),"
            if deleted_summary['consultations']:
                message += f" {deleted_summary['consultations']} consultation(s),"
            if deleted_summary['availabilities']:
                message += f" {deleted_summary['availabilities']} availability slot(s),"
            if deleted_summary['reviews']:
                message += f" {deleted_summary['reviews']} review(s),"
            if deleted_summary['applications']:
                message += f" {deleted_summary['applications']} application(s),"
            
            message = message.rstrip(',') + " deleted."
            
            self.message_user(request, message, level=messages.SUCCESS)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.is_superuser:
            if 'delete_selected' in actions:
                del actions['delete_selected']
            if 'delete_selected_users' in actions:
                del actions['delete_selected_users']
        return actions

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

# ==================== USER PROFILE ADMIN ====================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone', 'profile_status']
    list_filter = ['role']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'phone']
    readonly_fields = ['created_at', 'updated_at']

    def profile_status(self, obj):
        if obj.role == 'practitioner' and hasattr(obj.user, 'practitioner'):
            if obj.user.practitioner.is_verified:
                return format_html('<span style="color: #27ae60;">✅ Verified</span>')
            else:
                return format_html('<span style="color: #f39c12;">⏳ Pending</span>')
        return format_html('<span style="color: #3498db;">📋 Client</span>')
    profile_status.short_description = 'Status'

# ==================== PRACTITIONER ADMIN ====================

@admin.register(Practitioner)
class PractitionerAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'city', 'hourly_rate', 'currency',
        'years_of_experience', 'verification_status', 'profile_complete', 'practitioner_actions'
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

    def practitioner_actions(self, obj):
        if not obj.is_verified:
            return format_html(
                '<a class="button" href="/admin/NutriApp/practitioner/{}/approve/" '
                'style="background-color: #27ae60; color: white; padding: 3px 8px; '
                'border-radius: 4px; text-decoration: none;">✅ Approve</a>',
                obj.id
            )
        return format_html('<span style="color: #27ae60;">✅ Active</span>')
    practitioner_actions.short_description = 'Actions'

# ==================== PRACTITIONER APPLICATION ADMIN ====================

@admin.register(PractitionerApplication)
class PractitionerApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'practitioner', 'status_colored', 'submitted_at', 
        'reviewed_at', 'reviewed_by'
    ]
    list_filter = ['status']
    search_fields = ['practitioner__user__email', 'practitioner__user__first_name']
    readonly_fields = ['submitted_at', 'reviewed_at', 'reviewed_by']
    actions = [approve_applications, reject_applications]
    
    fieldsets = (
        ('Application Info', {
            'fields': ('practitioner', 'status', 'submitted_at')
        }),
        ('Review Details', {
            'fields': ('reviewed_at', 'reviewed_by', 'admin_notes', 'rejection_reason')
        }),
        ('Application Documents', {
            'fields': ('qualifications', 'experience_description', 
                      'id_document', 'certification_documents'),
            'classes': ('wide',)
        }),
    )

    def status_colored(self, obj):
        colors = {
            'pending': ('#f39c12', '⏳ Pending'),
            'approved': ('#27ae60', '✅ Approved'),
            'rejected': ('#e74c3c', '❌ Rejected'),
            'info_needed': ('#3498db', '📋 More Info')
        }
        color, text = colors.get(obj.status, ('#95a5a6', obj.status))
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; border-radius: 4px;">{}</span>',
            color, text
        )
    status_colored.short_description = 'Status'

    def save_model(self, request, obj, form, change):
        if 'status' in form.changed_data and obj.status in ['approved', 'rejected']:
            obj.reviewed_at = timezone.now()
            obj.reviewed_by = request.user
            
            if obj.status == 'approved':
                obj.approve(request.user)
            elif obj.status == 'rejected':
                obj.reject(request.user, obj.rejection_reason or 'Not specified')
        super().save_model(request, obj, form, change)

# ==================== SPECIALTY ADMIN ====================

@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'practitioner_count', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']

    def practitioner_count(self, obj):
        count = obj.practitioner.count()
        return format_html(
            '<span style="background-color: #3498db; color: white; padding: 2px 8px; border-radius: 10px;">{}</span>',
            count
        )
    practitioner_count.short_description = 'Practitioners'

# ==================== AVAILABILITY ADMIN ====================

@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = [
        'practitioner_info', 'recurrence_type', 'day_of_week',
        'specific_date', 'time_range', 'availability_status'
    ]
    list_filter = ['recurrence_type', 'is_available', 'day_of_week']
    search_fields = ['practitioner__user__email', 'notes']
    date_hierarchy = 'specific_date'
    readonly_fields = ['created_at', 'updated_at']

    def practitioner_info(self, obj):
        return f"{obj.practitioner.user.get_full_name()} ({obj.practitioner.user.email})"
    practitioner_info.short_description = 'Practitioner'

    def time_range(self, obj):
        return f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"
    time_range.short_description = 'Time'

    def availability_status(self, obj):
        if obj.is_available:
            return format_html('<span style="color: #27ae60;">✅ Available</span>')
        return format_html('<span style="color: #e74c3c;">❌ Unavailable</span>')
    availability_status.short_description = 'Status'

# ==================== CONSULTATION ADMIN ====================

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'client_info', 'practitioner_info', 'datetime',
        'status_colored', 'duration_minutes'
    ]
    list_filter = ['status', 'date']
    search_fields = ['client__email', 'practitioner__user__email']
    date_hierarchy = 'date'
    readonly_fields = ['version', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Participants', {
            'fields': ('client', 'practitioner')
        }),
        ('Schedule', {
            'fields': ('date', 'time', 'duration_minutes')
        }),
        ('Status', {
            'fields': ('status', 'version')
        }),
        ('Notes', {
            'fields': ('client_notes', 'practitioner_notes'),
            'classes': ('wide',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def client_info(self, obj):
        return f"{obj.client.get_full_name()} ({obj.client.email})"
    client_info.short_description = 'Client'

    def practitioner_info(self, obj):
        return f"{obj.practitioner.user.get_full_name()} ({obj.practitioner.user.email})"
    practitioner_info.short_description = 'Practitioner'

    def datetime(self, obj):
        return f"{obj.date.strftime('%Y-%m-%d')} at {obj.time.strftime('%H:%M')}"
    datetime.short_description = 'Date & Time'

    def status_colored(self, obj):
        colors = {
            'booked': ('#3498db', '📅 Booked'),
            'completed': ('#27ae60', '✅ Completed'),
            'cancelled': ('#e74c3c', '❌ Cancelled'),
            'no_show': ('#95a5a6', '🚫 No Show'),
        }
        color, text = colors.get(obj.status, ('#95a5a6', obj.status))
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; border-radius: 4px;">{}</span>',
            color, text
        )
    status_colored.short_description = 'Status'

# ==================== REVIEW ADMIN ====================

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['consultation', 'reviewer_info', 'rating_stars', 'short_comment', 'created_at']
    list_filter = ['rating']
    search_fields = ['reviewer__email', 'comment']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']

    def reviewer_info(self, obj):
        return f"{obj.reviewer.get_full_name()} ({obj.reviewer.email})"
    reviewer_info.short_description = 'Reviewer'

    def rating_stars(self, obj):
        stars = '⭐' * obj.rating
        return format_html(
            '<span style="color: #f39c12; font-size: 16px;">{}</span>',
            stars
        )
    rating_stars.short_description = 'Rating'

    def short_comment(self, obj):
        if obj.comment and len(obj.comment) > 50:
            return obj.comment[:50] + '...'
        return obj.comment or '-'
    short_comment.short_description = 'Comment'

# ==================== CUSTOM ADMIN SITE CONFIGURATION ====================

admin.site.site_header = 'NutriConnect Administration'
admin.site.site_title = 'NutriConnect Admin'
admin.site.index_title = 'Dashboard'