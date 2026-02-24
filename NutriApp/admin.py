from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.shortcuts import redirect
from django.urls import path
from .models import (
    User, UserProfile, Practitioner, Specialty,
    Availability, Consultation, Review
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
        
        # Send notification to practitioner
        # You can implement your notification logic here
        
        self.message_user(request, f"✅ Approved {practitioner.user.get_full_name()}", messages.SUCCESS)
        return redirect('admin:NutriApp_practitioner_changelist')
    
    def reject_practitioner(self, request, practitioner_id):
        practitioner = Practitioner.objects.get(id=practitioner_id)
        practitioner.is_verified = False
        practitioner.save()
        
        self.message_user(request, f"❌ Rejected {practitioner.user.get_full_name()}", messages.WARNING)
        return redirect('admin:NutriApp_practitioner_changelist')
    
    # Add a custom filter for pending practitioners
    class Media:
        css = {
            'all': ('admin/css/custom.css',)
        }

# ==============================================================================
# CUSTOM ADMIN VIEW FOR PENDING PRACTITIONERS
# ==============================================================================

class PendingPractitionerFilter(admin.SimpleListFilter):
    title = 'approval status'
    parameter_name = 'approval_status'
    
    def lookups(self, request, model_admin):
        return (
            ('pending', '⏳ Pending Approval'),
            ('approved', '✅ Approved'),
            ('rejected', '❌ Rejected'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'pending':
            return queryset.filter(is_verified=False)
        if self.value() == 'approved':
            return queryset.filter(is_verified=True)
        if self.value() == 'rejected':
            return queryset.filter(is_verified=False)  # You might want a rejected field
        return queryset

# Register the filter by adding it to list_filter
# list_filter = [PendingPractitionerFilter, ...]

# ==============================================================================
# DASHBOARD CUSTOMIZATION FOR APPROVAL QUEUE
# ==============================================================================

# Add to your existing admin.py or create a new admin_dashboard.py
from django.contrib.admin import AdminSite
from django.template.response import TemplateResponse

class NutriConnectAdminSite(AdminSite):
    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        
        # Add pending count to dashboard
        pending_count = Practitioner.objects.filter(is_verified=False).count()
        
        # You can customize the dashboard template
        return app_list
    
    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['pending_practitioners'] = Practitioner.objects.filter(is_verified=False).count()
        extra_context['recent_practitioners'] = Practitioner.objects.order_by('-created_at')[:5]
        return super().index(request, extra_context=extra_context)

# ==============================================================================
# CUSTOM ADMIN TEMPLATE (templates/admin/practitioner_approval.html)
# ==============================================================================

"""
Create this template to show pending approvals:

{% extends "admin/base_site.html" %}
{% load i18n static %}

{% block content %}
<div style="padding: 20px;">
    <h1 style="margin-bottom: 20px;">⏳ Pending Practitioner Approvals</h1>
    
    <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr style="background: #f8f9fa;">
                    <th style="padding: 12px; text-align: left;">Name</th>
                    <th style="padding: 12px; text-align: left;">Email</th>
                    <th style="padding: 12px; text-align: left;">City</th>
                    <th style="padding: 12px; text-align: left;">Experience</th>
                    <th style="padding: 12px; text-align: left;">Rate</th>
                    <th style="padding: 12px; text-align: left;">Applied</th>
                    <th style="padding: 12px; text-align: left;">Actions</th>
                </tr>
            </thead>
            <tbody>
                {% for practitioner in pending_practitioners %}
                <tr style="border-bottom: 1px solid #dee2e6;">
                    <td style="padding: 12px;">{{ practitioner.user.get_full_name }}</td>
                    <td style="padding: 12px;">{{ practitioner.user.email }}</td>
                    <td style="padding: 12px;">{{ practitioner.city|default:"—" }}</td>
                    <td style="padding: 12px;">{{ practitioner.years_of_experience }} years</td>
                    <td style="padding: 12px;">{{ practitioner.currency }} {{ practitioner.hourly_rate }}</td>
                    <td style="padding: 12px;">{{ practitioner.created_at|date:"M d, Y" }}</td>
                    <td style="padding: 12px;">
                        <a href="{% url 'admin:approve-practitioner' practitioner.id %}" 
                           style="background: #10b981; color: white; padding: 5px 10px; border-radius: 5px; text-decoration: none; margin-right: 5px;">✅ Approve</a>
                        <a href="{% url 'admin:reject-practitioner' practitioner.id %}" 
                           style="background: #ef4444; color: white; padding: 5px 10px; border-radius: 5px; text-decoration: none;">❌ Reject</a>
                    </td>
                </tr>
                {% empty %}
                <tr>
                    <td colspan="7" style="padding: 40px; text-align: center; color: #6c757d;">
                        No pending approvals 🎉
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
"""