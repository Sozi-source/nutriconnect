from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
# ==================== ADMIN ACTIONS ====================

@admin.action(description="✅ Approve selected applications (auto-create practitioners)")
def approve_applications(modeladmin, request, queryset):
    approved_count = 0
    error_count = 0

    for application in queryset.filter(status='pending'):
        try:
            with transaction.atomic():
                # 1. Update user profile role
                profile = application.user.profile
                profile.role = 'practitioner'
                profile.save()

                # 2. Create practitioner profile
                practitioner = Practitioner.objects.create(
                    user=application.user,
                    bio=application.bio,
                    city=application.city,
                    hourly_rate=application.hourly_rate,
                    years_of_experience=application.years_of_experience,
                    currency='KES',
                    is_verified=True,
                    profile_complete=True
                )

                # 3. Add specialties
                practitioner.specialties.set(application.specialties.all())

                # 4. Update application status
                application.status = 'approved'
                application.admin_notes = f"Approved by {request.user.email} on {timezone.now().strftime('%Y-%m-%d %H:%M')}"
                application.reviewed_at = timezone.now()
                application.reviewed_by = request.user
                application.save()

                approved_count += 1

        except Exception as e:
            error_count += 1
            modeladmin.message_user(
                request,
                f"Error approving {application.user.email}: {str(e)}",
                level=messages.ERROR
            )

    modeladmin.message_user(
        request,
        f"✅ Approved {approved_count} applications. {error_count} errors.",
        level=messages.SUCCESS if approved_count > 0 else messages.WARNING
    )


@admin.action(description="❌ Reject selected applications")
def reject_applications(modeladmin, request, queryset):
    rejected_count = 0

    for application in queryset.filter(status='pending'):
        application.status = 'rejected'
        application.admin_notes = f"Rejected by {request.user.email} on {timezone.now().strftime('%Y-%m-%d %H:%M')}"
        application.reviewed_at = timezone.now()
        application.reviewed_by = request.user
        application.save()
        rejected_count += 1

    modeladmin.message_user(
        request,
        f"❌ Rejected {rejected_count} applications.",
        level=messages.WARNING
    )


@admin.action(description="📝 Mark as 'More Info Needed'")
def request_more_info(modeladmin, request, queryset):
    updated_count = 0

    for application in queryset.filter(status='pending'):
        application.status = 'more_info'
        application.admin_notes = f"Additional information requested by {request.user.email} on {timezone.now().strftime('%Y-%m-%d %H:%M')}"
        application.reviewed_at = timezone.now()
        application.reviewed_by = request.user
        application.save()
        updated_count += 1

    modeladmin.message_user(
        request,
        f"📝 Requested more info for {updated_count} applications.",
        level=messages.INFO
    )


# ==================== USER ADMIN ====================

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_active', 'is_staff', 'has_application']
    list_filter = ['is_active', 'is_staff']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['email']

    def has_application(self, obj):
        try:
            if hasattr(obj, 'practitioner_application'):
                return format_html(
                    '<span style="color: {};">{}</span>',
                    'orange' if obj.practitioner_application.status == 'pending' else 'green',
                    obj.practitioner_application.status
                )
        except:
            pass
        return 'No'
    has_application.short_description = 'Application'


# ==================== USER PROFILE ADMIN ====================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone']
    list_filter = ['role']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'phone']


# ==================== PRACTITIONER APPLICATION ADMIN ====================

@admin.register(PractitionerApplication)
class PractitionerApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'user_email', 'user_name', 'city', 'hourly_rate',
        'years_of_experience', 'status_colored', 'created_at'
    ]
    list_filter = ['status', 'city', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'license_number']
    readonly_fields = ['created_at', 'updated_at', 'reviewed_at', 'reviewed_by']
    actions = [approve_applications, reject_applications, request_more_info]
    filter_horizontal = ['specialties']

    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Professional Details', {
            'fields': ('bio', 'city', 'hourly_rate', 'years_of_experience')
        }),
        ('Credentials', {
            'fields': ('qualifications', 'license_number', 'specialties')
        }),
        ('Application Status', {
            'fields': ('status', 'admin_notes', 'reviewed_at', 'reviewed_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'

    def user_name(self, obj):
        return obj.user.get_full_name() or obj.user.email
    user_name.short_description = 'Name'
    user_name.admin_order_field = 'user__first_name'

    def status_colored(self, obj):
        colors = {
            'pending': '#f39c12',  # orange
            'approved': '#27ae60',  # green
            'rejected': '#e74c3c',  # red
            'more_info': '#3498db'  # blue
        }
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            colors.get(obj.status, '#95a5a6'),
            obj.get_status_display()
        )
    status_colored.short_description = 'Status'
    status_colored.admin_order_field = 'status'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)


# ==================== PRACTITIONER ADMIN ====================

@admin.register(Practitioner)
class PractitionerAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'city', 'hourly_rate', 'currency',
        'years_of_experience', 'is_verified', 'profile_complete'
    ]
    list_filter = ['is_verified', 'profile_complete', 'city', 'currency']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'city']
    filter_horizontal = ['specialties']
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


# ==================== SPECIALTY ADMIN ====================

@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'practitioner_count', 'application_count']
    search_fields = ['name']

    def practitioner_count(self, obj):
        count = obj.practitioner.count()
        return format_html('<b>{}</b>', count)
    practitioner_count.short_description = 'Practitioners'

    def application_count(self, obj):
        count = obj.practitionerapplication_set.count()
        return format_html('<b>{}</b>', count)
    application_count.short_description = 'Applications'


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


# ==================== REVIEW ADMIN ====================

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['consultation', 'reviewer', 'rating', 'created_at']
    list_filter = ['rating']
    search_fields = ['reviewer__email', 'comment']
    date_hierarchy = 'created_at'
# ==================== PRACTITIONER APPLICATION ADMIN ====================

@admin.register(PractitionerApplication)
class PractitionerApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'user_email', 'user_name', 'city', 'hourly_rate',
        'years_of_experience', 'status_colored', 'created_at'
    ]
    list_filter = ['status', 'city', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'license_number']
    readonly_fields = ['created_at', 'updated_at', 'reviewed_at', 'reviewed_by']
    filter_horizontal = ['specialties']

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'

    def user_name(self, obj):
        return obj.user.get_full_name() or obj.user.email
    user_name.short_description = 'Name'

    def status_colored(self, obj):
        colors = {
            'pending': '#f39c12',
            'approved': '#27ae60',
            'rejected': '#e74c3c',
            'more_info': '#3498db'
        }
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; border-radius: 4px;">{}</span>',
            colors.get(obj.status, '#95a5a6'),
            obj.get_status_display()
        )
    status_colored.short_description = 'Status'
