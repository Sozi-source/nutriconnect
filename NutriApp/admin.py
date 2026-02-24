from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, UserProfile, Practitioner, Specialty,
    Availability, Consultation, Review
)

# ==================== SIMPLE ADMIN ACTIONS ====================

def approve_practitioners(modeladmin, request, queryset):
    count = queryset.update(is_verified=True)
    modeladmin.message_user(request, f"✅ Approved {count} practitioner(s).")
approve_practitioners.short_description = "Approve selected practitioners"

def reject_practitioners(modeladmin, request, queryset):
    count = queryset.update(is_verified=False)
    modeladmin.message_user(request, f"❌ Rejected {count} practitioner(s).")
reject_practitioners.short_description = "Reject selected practitioners"

# ==================== MODEL REGISTRATIONS ====================

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

@admin.register(Practitioner)
class PractitionerAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'hourly_rate', 'is_verified', 'profile_complete']
    list_filter = ['is_verified', 'profile_complete', 'city']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'city']
    filter_horizontal = ['specialties']
    readonly_fields = ['created_at', 'updated_at']
    actions = [approve_practitioners, reject_practitioners]

@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ['practitioner', 'recurrence_type', 'start_time', 'end_time', 'is_available']
    list_filter = ['recurrence_type', 'is_available']
    search_fields = ['practitioner__user__email']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ['client', 'practitioner', 'date', 'time', 'status']
    list_filter = ['status', 'date']
    search_fields = ['client__email', 'practitioner__user__email']
    readonly_fields = ['version', 'created_at', 'updated_at']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['consultation', 'reviewer', 'rating', 'created_at']
    list_filter = ['rating']
    search_fields = ['reviewer__email']
    readonly_fields = ['created_at', 'updated_at']

# ==================== CUSTOM ADMIN SITE CONFIGURATION ====================

admin.site.site_header = 'NutriConnect Administration'
admin.site.site_title = 'NutriConnect Admin'
admin.site.index_title = 'Dashboard'