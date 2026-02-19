from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import (
    User, UserProfile, Specialty, Practitioner, 
    Availability, Consultation, Review
)

# Custom User Admin (since you're using email as username)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'get_role', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__role')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
    
    def get_role(self, obj):
        if hasattr(obj, 'profile'):
            if obj.profile.role == 'practitioner':
                return format_html('<span style="color: #28a745;">🏥 Practitioner</span>')
            return format_html('<span style="color: #17a2b8;">👤 Client</span>')
        return format_html('<span style="color: #6c757d;">⚠️ No Profile</span>')
    get_role.short_description = 'Role'

# UserProfile Admin
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone')
    list_filter = ('role',)
    search_fields = ('user__email', 'user__first_name', 'user__last_name')

# Specialty Admin
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name', 'description_short', 'practitioner_count')
    search_fields = ('name',)
    
    def description_short(self, obj):
        return obj.description[:50] + '...' if obj.description and len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'
    
    def practitioner_count(self, obj):
        count = obj.practitioner_set.count()
        return format_html('<b>{}</b>', count)
    practitioner_count.short_description = 'Practitioners'

# Practitioner Admin
class PractitionerAdmin(admin.ModelAdmin):
    list_display = (
        'user_email', 'user_name', 'city', 'specialties_list', 
        'hourly_rate', 'currency', 'years_of_experience', 
        'verification_badge', 'created_at'
    )
    list_filter = ('is_verified', 'city', 'specialties', 'currency')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'bio', 'city')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user',)
    filter_horizontal = ('specialties',)
    actions = ['approve_practitioners', 'unapprove_practitioners']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'bio')
        }),
        ('Professional Details', {
            'fields': ('specialties', 'years_of_experience', 'is_verified', 'profile_complete')
        }),
        ('Location & Rates', {
            'fields': ('city', 'hourly_rate', 'currency')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.admin_order_field = 'user__email'
    
    def user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    user_name.short_description = 'Name'
    user_name.admin_order_field = 'user__first_name'
    
    def specialties_list(self, obj):
        return ", ".join([s.name for s in obj.specialties.all()]) or "—"
    specialties_list.short_description = 'Specialties'
    
    def verification_badge(self, obj):
        if obj.is_verified:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 5px 10px; '
                'border-radius: 3px; font-weight: bold;">✓ VERIFIED</span>'
            )
        return format_html(
                '<span style="background: #ffc107; color: black; padding: 5px 10px; '
                'border-radius: 3px; font-weight: bold;">⏳ PENDING</span>'
        )
    verification_badge.short_description = 'Status'
    
    def approve_practitioners(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'✅ {updated} practitioner(s) approved successfully.')
    approve_practitioners.short_description = "Approve selected practitioners"
    
    def unapprove_practitioners(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'⏳ {updated} practitioner(s) set to pending.')
    unapprove_practitioners.short_description = "Set as pending"

# Availability Admin
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ('practitioner_info', 'day_of_week', 'start_time', 'end_time')
    list_filter = ('day_of_week', 'practitioner__city')
    search_fields = ('practitioner__user__email', 'practitioner__user__first_name')
    raw_id_fields = ('practitioner',)
    
    def practitioner_info(self, obj):
        return f"{obj.practitioner.user.get_full_name()} ({obj.practitioner.city})"
    practitioner_info.short_description = 'Practitioner'

# Consultation Admin
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('id', 'client_info', 'practitioner_info', 'date', 'time', 'status_badge')
    list_filter = ('status', 'date', 'practitioner__city')
    search_fields = ('client__email', 'practitioner__user__email', 'client_notes')
    raw_id_fields = ('client', 'practitioner')
    readonly_fields = ('created_at', 'updated_at', 'version')
    
    fieldsets = (
        ('Appointment Details', {
            'fields': ('client', 'practitioner', 'date', 'time', 'duration_minutes', 'status')
        }),
        ('Notes', {
            'fields': ('client_notes', 'practitioner_notes')
        }),
        ('System', {
            'fields': ('version', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def client_info(self, obj):
        return obj.client.get_full_name() or obj.client.email
    client_info.short_description = 'Client'
    
    def practitioner_info(self, obj):
        return f"{obj.practitioner.user.get_full_name()} ({obj.practitioner.city})"
    practitioner_info.short_description = 'Practitioner'
    
    def status_badge(self, obj):
        colors = {
            'booked': ('#ffc107', 'BOOKED'),
            'completed': ('#28a745', 'COMPLETED'),
            'cancelled': ('#dc3545', 'CANCELLED'),
            'no_show': ('#6c757d', 'NO SHOW'),
        }
        color, text = colors.get(obj.status, ('#6c757d', obj.status.upper()))
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 0.8em;">{}</span>',
            color, text
        )
    status_badge.short_description = 'Status'

# Review Admin
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('consultation_info', 'reviewer_email', 'rating_stars', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('reviewer__email', 'comment')
    raw_id_fields = ('consultation', 'reviewer')
    
    def consultation_info(self, obj):
        return f"Consultation #{obj.consultation.id} - {obj.consultation.date}"
    consultation_info.short_description = 'Consultation'
    
    def reviewer_email(self, obj):
        return obj.reviewer.email if obj.reviewer else 'Anonymous'
    reviewer_email.short_description = 'Reviewer'
    
    def rating_stars(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        colors = ['#dc3545', '#ffc107', '#ffc107', '#28a745', '#28a745']
        return format_html(
            '<span style="color: {}; font-size: 1.2em;">{}</span>',
            colors[obj.rating - 1], stars
        )
    rating_stars.short_description = 'Rating'

# Register all models
admin.site.register(User, UserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Specialty, SpecialtyAdmin)
admin.site.register(Practitioner, PractitionerAdmin)
admin.site.register(Availability, AvailabilityAdmin)
admin.site.register(Consultation, ConsultationAdmin)
admin.site.register(Review, ReviewAdmin)

# Customize admin site
admin.site.site_header = "NutriConnect Administration"
admin.site.site_title = "NutriConnect Admin Portal"
admin.site.index_title = "Welcome to NutriConnect Admin Dashboard"