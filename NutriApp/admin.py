from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.shortcuts import redirect
from django.urls import path
from django.utils import timezone
from .models import (
    User, UserProfile, Practitioner, Specialty,
    Availability, Consultation, Review, PractitionerApplication
)

# ==============================================================================
# ADMIN ACTIONS FOR BULK APPROVAL
# ==============================================================================

def approve_practitioners(modeladmin, request, queryset):
    count = queryset.update(is_verified=True)
    # Send notifications to approved practitioners
    for practitioner in queryset:
        # Create notification logic here
        pass
    modeladmin.message_user(request, f"✅ Approved {count} practitioner(s).", messages.SUCCESS)
approve_practitioners.short_description = "✅ Approve selected practitioners"

def reject_practitioners(modeladmin, request, queryset):
    count = queryset.update(is_verified=False)
    modeladmin.message_user(request, f"❌ Rejected {count} practitioner(s).", messages.WARNING)
reject_practitioners.short_description = "❌ Reject selected practitioners"

# ==============================================================================
# USER ADMIN
# ==============================================================================

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_active', 'is_staff']
    list_filter = ['is_active', 'is_staff']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['email']
    
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


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone']
    list_filter = ['role']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'phone']


# ==============================================================================
# PRACTITIONER ADMIN WITH APPROVAL WORKFLOW
# ==============================================================================

@admin.register(Practitioner)
class PractitionerAdmin(admin.ModelAdmin):
    # Custom admin URLs for approval actions
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:practitioner_id>/approve/',
                self.admin_site.admin_view(self.approve_practitioner),
                name='approve-practitioner',
            ),
            path(
                '<int:practitioner_id>/reject/',
                self.admin_site.admin_view(self.reject_practitioner),
                name='reject-practitioner',
            ),
        ]
        return custom_urls + urls
    
    # List display with approval status and actions
    list_display = [
        'practitioner_name',
        'email_display',
        'city_display',
        'rate_display',
        'experience_display',
        'verification_badge',
        'profile_status',
        'specialties_list',
        'approval_actions'
    ]
    
    list_filter = [
        'is_verified',
        'profile_complete',
        'city',
        'currency',
        ('created_at', admin.DateFieldListFilter),
    ]
    
    search_fields = [
        'user__email',
        'user__first_name',
        'user__last_name',
        'city',
        'bio'
    ]
    
    filter_horizontal = ['specialties']
    readonly_fields = ['created_at', 'updated_at', 'user_profile_link']
    actions = [approve_practitioners, reject_practitioners]
    list_per_page = 25
    list_select_related = ['user']
    
    # Fieldsets organized for approval workflow
    fieldsets = (
        ('👤 PRACTITIONER INFORMATION', {
            'fields': ('user_profile_link',),
            'classes': ['wide']
        }),
        ('📍 LOCATION & RATES', {
            'fields': ('city', ('hourly_rate', 'currency')),
            'classes': ['wide']
        }),
        ('📝 PROFESSIONAL DETAILS', {
            'fields': ('bio', 'years_of_experience', 'specialties'),
            'classes': ['wide']
        }),
        ('✅ APPROVAL STATUS', {
            'fields': ('is_verified', 'profile_complete'),
            'classes': ['wide', 'approval-section'],
            'description': 'Set is_verified = True to approve practitioner'
        }),
        ('📅 TIMESTAMPS', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )
    
    # Custom display methods
    def practitioner_name(self, obj):
        name = obj.user.get_full_name() or obj.user.email
        if not obj.is_verified:
            return format_html(
                '<span style="font-weight: bold;">{} <span style="color: #f59e0b; font-size: 0.8em;">(Pending)</span></span>',
                name
            )
        return format_html('<span style="font-weight: bold;">{} ✅</span>', name)
    practitioner_name.short_description = 'Name'
    practitioner_name.admin_order_field = 'user__first_name'
    
    def email_display(self, obj):
        return format_html(
            '<a href="mailto:{}" style="color: #3b82f6;">{}</a>',
            obj.user.email,
            obj.user.email
        )
    email_display.short_description = 'Email'
    
    def city_display(self, obj):
        if obj.city:
            return format_html('📍 {}', obj.city)
        return '—'
    city_display.short_description = 'City'
    
    def rate_display(self, obj):
        if obj.hourly_rate:
            return format_html(
                '<span style="font-weight: bold; color: #10b981;">{}{}/hr</span>',
                obj.currency,
                obj.hourly_rate
            )
        return '—'
    rate_display.short_description = 'Rate'
    
    def experience_display(self, obj):
        if obj.years_of_experience:
            return f"{obj.years_of_experience} years"
        return '—'
    experience_display.short_description = 'Exp'
    
    def verification_badge(self, obj):
        if obj.is_verified:
            return format_html(
                '<span style="background-color: #10b981; color: white; padding: 3px 8px; border-radius: 12px; font-size: 0.8em; font-weight: bold;">✅ VERIFIED</span>'
            )
        return format_html(
            '<span style="background-color: #f59e0b; color: white; padding: 3px 8px; border-radius: 12px; font-size: 0.8em; font-weight: bold;">⏳ PENDING</span>'
        )
    verification_badge.short_description = 'Status'
    
    def profile_status(self, obj):
        if obj.profile_complete:
            return format_html('<span style="color: #10b981;">✓ Complete</span>')
        return format_html('<span style="color: #ef4444;">✗ Incomplete</span>')
    profile_status.short_description = 'Profile'
    
    def specialties_list(self, obj):
        specialties = obj.specialties.all()[:3]
        if specialties:
            names = [s.name for s in specialties]
            display = ', '.join(names)
            if obj.specialties.count() > 3:
                display += f' +{obj.specialties.count() - 3} more'
            return display
        return '—'
    specialties_list.short_description = 'Specialties'
    
    def user_profile_link(self, obj):
        url = reverse('admin:NutriApp_user_change', args=[obj.user.id])
        return format_html(
            '<a href="{}" style="font-weight: bold;">View Full User Profile →</a>',
            url
        )
    user_profile_link.short_description = ''
    
    def approval_actions(self, obj):
        if not obj.is_verified:
            approve_url = reverse('admin:approve-practitioner', args=[obj.id])
            reject_url = reverse('admin:reject-practitioner', args=[obj.id])
            return format_html(
                '<a class="button" href="{}" style="background-color: #10b981; color: white; padding: 5px 10px; border-radius: 5px; margin-right: 5px; text-decoration: none;">✅ Approve</a>'
                '<a class="button" href="{}" style="background-color: #ef4444; color: white; padding: 5px 10px; border-radius: 5px; text-decoration: none;">❌ Reject</a>',
                approve_url, reject_url
            )
        return format_html(
            '<span style="color: #10b981;">✓ Approved</span>'
        )
    approval_actions.short_description = 'Actions'
    
    # Custom admin views for approval
    def approve_practitioner(self, request, practitioner_id):
        practitioner = Practitioner.objects.get(id=practitioner_id)
        practitioner.is_verified = True
        practitioner.save()
        
        self.message_user(request, f"✅ Approved {practitioner.user.get_full_name()}", messages.SUCCESS)
        return redirect('admin:NutriApp_practitioner_changelist')
    
    def reject_practitioner(self, request, practitioner_id):
        practitioner = Practitioner.objects.get(id=practitioner_id)
        practitioner.is_verified = False
        practitioner.save()
        
        self.message_user(request, f"❌ Rejected {practitioner.user.get_full_name()}", messages.WARNING)
        return redirect('admin:NutriApp_practitioner_changelist')
    
    class Media:
        css = {
            'all': ('admin/css/custom.css',)
        }


# ==============================================================================
# SPECIALTY ADMIN
# ==============================================================================

@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


# ==============================================================================
# AVAILABILITY ADMIN
# ==============================================================================

@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ['practitioner', 'recurrence_type', 'start_time', 'end_time', 'is_available']
    list_filter = ['recurrence_type', 'is_available']
    search_fields = ['practitioner__user__email']
    readonly_fields = ['created_at', 'updated_at']


# ==============================================================================
# CONSULTATION ADMIN
# ==============================================================================

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ['client', 'practitioner', 'date', 'time', 'status']
    list_filter = ['status', 'date']
    search_fields = ['client__email', 'practitioner__user__email']
    readonly_fields = ['version', 'created_at', 'updated_at']


# ==============================================================================
# REVIEW ADMIN
# ==============================================================================

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['consultation', 'reviewer', 'rating', 'created_at']
    list_filter = ['rating']
    search_fields = ['reviewer__email']
    readonly_fields = ['created_at', 'updated_at']


# ==============================================================================
# PRACTITIONER APPLICATION ADMIN
# ==============================================================================

@admin.register(PractitionerApplication)
class PractitionerApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'practitioner_name',
        'professional_title',
        'status_badge',
        'submitted_at_display',
        'reviewed_at_display',
    ]
    
    list_filter = [
        'status',
        ('submitted_at', admin.DateFieldListFilter),
    ]
    
    search_fields = [
        'practitioner__user__email',
        'practitioner__user__first_name',
        'practitioner__user__last_name',
        'professional_title',
        'qualifications'
    ]
    
    readonly_fields = [
        'practitioner',
        'created_at',
        'updated_at',
        'submitted_at',
        'reviewed_at',
        'reviewed_by',
        'application_details'
    ]
    
    fieldsets = (
        ('👤 APPLICANT', {
            'fields': ('practitioner', 'application_details'),
        }),
        ('📋 PROFESSIONAL INFO', {
            'fields': ('professional_title', 'qualifications', 'experience_description', 'specialized_areas'),
        }),
        ('🔗 ONLINE PRESENCE', {
            'fields': ('linkedin_url', 'website_url'),
        }),
        ('📄 DOCUMENTS', {
            'fields': ('id_document', 'certification_documents', 'profile_photo'),
        }),
        ('✅ REVIEW & STATUS', {
            'fields': ('status', 'admin_notes', 'rejection_reason', 'reviewed_by', 'reviewed_at'),
            'classes': ('wide',),
            'description': 'Change status to approve or reject this application'
        }),
        ('📅 TIMESTAMPS', {
            'fields': ('created_at', 'updated_at', 'submitted_at'),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['approve_applications', 'reject_applications', 'mark_as_pending']
    
    def practitioner_name(self, obj):
        name = obj.practitioner.user.get_full_name() or obj.practitioner.user.email
        return format_html('<strong>{}</strong>', name)
    practitioner_name.short_description = 'Practitioner'
    practitioner_name.admin_order_field = 'practitioner__user__email'
    
    def status_badge(self, obj):
        colors = {
            'draft': ('#6c757d', '📝 Draft'),
            'pending': ('#f59e0b', '⏳ Pending'),
            'approved': ('#10b981', '✅ Approved'),
            'rejected': ('#ef4444', '❌ Rejected'),
            'info_needed': ('#3b82f6', 'ℹ️ Info Needed'),
        }
        color, text = colors.get(obj.status, ('#6c757d', obj.status))
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 0.8em; font-weight: bold;">{}</span>',
            color, text
        )
    status_badge.short_description = 'Status'
    
    def submitted_at_display(self, obj):
        if obj.submitted_at:
            return obj.submitted_at.strftime("%b %d, %Y %H:%M")
        return '—'
    submitted_at_display.short_description = 'Submitted'
    
    def reviewed_at_display(self, obj):
        if obj.reviewed_at:
            return obj.reviewed_at.strftime("%b %d, %Y %H:%M")
        return '—'
    reviewed_at_display.short_description = 'Reviewed'
    
    def application_details(self, obj):
        return format_html(
            '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
            '<p><strong>Email:</strong> {}</p>'
            '<p><strong>Phone:</strong> {}</p>'
            '<p><strong>City:</strong> {}</p>'
            '<p><strong>Experience:</strong> {} years</p>'
            '<p><strong>Hourly Rate:</strong> {} {}</p>'
            '</div>',
            obj.practitioner.user.email,
            obj.practitioner.user.profile.phone or 'Not provided',
            obj.practitioner.city or 'Not provided',
            obj.practitioner.years_of_experience,
            obj.practitioner.currency,
            obj.practitioner.hourly_rate
        )
    application_details.short_description = 'Practitioner Details'
    
    def approve_applications(self, request, queryset):
        for app in queryset:
            app.status = 'approved'
            app.reviewed_at = timezone.now()
            app.reviewed_by = request.user
            app.save()
            # Also verify the practitioner
            app.practitioner.is_verified = True
            app.practitioner.save()
        self.message_user(request, f"✅ Approved {queryset.count()} application(s)", messages.SUCCESS)
    approve_applications.short_description = "✅ Approve selected applications"
    
    def reject_applications(self, request, queryset):
        for app in queryset:
            app.status = 'rejected'
            app.reviewed_at = timezone.now()
            app.reviewed_by = request.user
            app.save()
        self.message_user(request, f"❌ Rejected {queryset.count()} application(s)", messages.WARNING)
    reject_applications.short_description = "❌ Reject selected applications"
    
    def mark_as_pending(self, request, queryset):
        queryset.update(status='pending')
        self.message_user(request, f"⏳ Marked {queryset.count()} application(s) as pending")
    mark_as_pending.short_description = "⏳ Mark as pending"
    
    def save_model(self, request, obj, form, change):
        if obj.status == 'approved' and not obj.reviewed_at:
            obj.reviewed_at = timezone.now()
            obj.reviewed_by = request.user
            # Also verify the practitioner
            obj.practitioner.is_verified = True
            obj.practitioner.save()
        super().save_model(request, obj, form, change)


# ==============================================================================
# CUSTOM ADMIN SITE CONFIGURATION
# ==============================================================================

admin.site.site_header = '🥗 NutriConnect Administration'
admin.site.site_title = 'NutriConnect Admin'
admin.site.index_title = 'Dashboard'