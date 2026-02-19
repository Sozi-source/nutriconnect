from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import (
    User, UserProfile, Specialty, Practitioner, 
    Availability, Consultation, Review
)

# Custom User Admin
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
    list_display = ('name', 'description')
    search_fields = ('name',)

# Practitioner Admin
class PractitionerAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'user_name', 'city', 'get_specialties', 'hourly_rate', 'currency', 'is_verified')
    list_filter = ('is_verified', 'city', 'currency')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'bio', 'city')
    actions = ['approve_practitioners']
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    
    def user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    user_name.short_description = 'Name'
    
    def get_specialties(self, obj):
        return ", ".join([s.name for s in obj.specialties.all()]) or "—"
    get_specialties.short_description = 'Specialties'
    
    def approve_practitioners(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'✅ {updated} practitioner(s) approved.')
    approve_practitioners.short_description = "Approve selected practitioners"

# Availability Admin
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ('practitioner', 'day_of_week', 'start_time', 'end_time')
    list_filter = ('day_of_week',)
    search_fields = ('practitioner__user__email',)

# Consultation Admin
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'practitioner', 'date', 'time', 'status')
    list_filter = ('status', 'date')
    search_fields = ('client__email', 'practitioner__user__email')
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

# Review Admin
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('consultation', 'reviewer', 'rating', 'created_at')
    list_filter = ('rating',)
    search_fields = ('reviewer__email', 'comment')

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
admin.site.site_title = "NutriConnect Admin"
admin.site.index_title = "Welcome to NutriConnect Admin Portal"