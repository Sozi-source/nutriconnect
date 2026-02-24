from django.urls import path, include
from django.http import JsonResponse
from . import views
from rest_framework.decorators import api_view

# ==============================================================================
# ROOT API ENDPOINT
# ==============================================================================

def api_root(request):
    """Root API endpoint with navigation links"""
    base_url = request.build_absolute_uri('/').rstrip('/')
    
    return JsonResponse({
        "message": "Welcome to NutriConnect API",
        "version": "2.0",
        "documentation": f"{base_url}/docs/",
        "base_url": base_url,
        "endpoints": {
            # Health & Info
            "Health Check": f"{base_url}/health/",
            
            # Authentication
            "Register": f"{base_url}/register/",
            "Login": f"{base_url}/login/",
            "Logout": f"{base_url}/logout/",
            "Profile": f"{base_url}/profile/",
            
            # Resources
            "Specialties": f"{base_url}/specialties/",
            "Practitioners": f"{base_url}/practitioners/",
            "Availability": f"{base_url}/availability/",
            "Consultations": f"{base_url}/consultations/",
            
            # Reviews
            "Reviews": f"{base_url}/reviews/",
            
            # Notifications
            "Notifications": f"{base_url}/notifications/",
            "Notification Unread Count": f"{base_url}/notifications/unread-count/",
            
            # Practitioner Applications
            "My Application": f"{base_url}/practitioners/application/me/",
            "Create Application": f"{base_url}/practitioners/application/create/",
            "Application Status": f"{base_url}/practitioners/application/status/",
            
            # Admin
            "Admin Pending Practitioners": f"{base_url}/admin/practitioners/pending/",
            "Admin Approve Practitioner": f"{base_url}/admin/practitioners/<id>/approve/",
            "Admin Reject Practitioner": f"{base_url}/admin/practitioners/<id>/reject/",
            "Admin Applications": f"{base_url}/admin/applications/",
        }
    })


# ==============================================================================
# PRACTITIONER URL PATTERNS
# ==============================================================================

practitioner_patterns = [
    # List and detail
    path('', views.PractitionerListView.as_view(), name='practitioner-list'),
    path('<int:pk>/', views.PractitionerDetailView.as_view(), name='practitioner-detail'),
    path('me/', views.MyPractitionerProfileView.as_view(), name='practitioner-me'),
    
    # Practitioner verification (for admin)
    path('<int:pk>/verify/', views.PractitionerVerificationView.as_view(), name='practitioner-verify'),
    
    # Practitioner availability (public)
    path('<int:pk>/availability/', views.PractitionerAvailabilityView.as_view(), name='practitioner-availability'),
    
    # Practitioner reviews
    path('<int:pk>/reviews/', views.PractitionerReviewsView.as_view(), name='practitioner-reviews'),
    
    # ========== PRACTITIONER APPLICATION URLS (nested under practitioners) ==========
    path('application/create/', views.PractitionerApplicationCreateView.as_view(), name='practitioner-application-create'),
    path('application/me/', views.PractitionerApplicationDetailView.as_view(), name='practitioner-application-detail'),
    path('application/submit/', views.PractitionerApplicationSubmitView.as_view(), name='practitioner-application-submit'),
    path('application/status/', views.PractitionerApplicationStatusView.as_view(), name='practitioner-application-status'),
]


# ==============================================================================
# CONSULTATION URL PATTERNS
# ==============================================================================

consultation_patterns = [
    # Main consultations
    path('', views.ConsultationListCreateView.as_view(), name='consultation-list'),
    path('<int:pk>/', views.ConsultationDetailView.as_view(), name='consultation-detail'),
    path('<int:pk>/status/', views.ConsultationUpdateStatusView.as_view(), name='consultation-status'),
    
    # Filtered consultations
    path('my-client/', views.MyClientConsultationsView.as_view(), name='client-consultations'),
    path('my-practitioner/', views.MyPractitionerConsultationsView.as_view(), name='practitioner-consultations'),
    path('completed/no-review/', views.CompletedConsultationsNoReviewView.as_view(), name='completed-no-review'),
    
    # Metrics
    path('metrics/', views.ConsultationMetricsView.as_view(), name='consultation-metrics'),
]


# ==============================================================================
# REVIEW URL PATTERNS
# ==============================================================================

review_patterns = [
    # Create review
    path('create/', views.ReviewCreateView.as_view(), name='review-create'),
    
    # User's reviews
    path('my-reviews/', views.MyReviewsView.as_view(), name='my-reviews'),
]


# ==============================================================================
# NOTIFICATION URL PATTERNS
# ==============================================================================

notification_patterns = [
    # List and detail
    path('', views.NotificationListView.as_view(), name='notification-list'),
    path('<int:pk>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    
    # Actions
    path('<int:pk>/read/', views.NotificationMarkReadView.as_view(), name='notification-mark-read'),
    path('mark-all-read/', views.NotificationMarkAllReadView.as_view(), name='notification-mark-all-read'),
    path('unread-count/', views.NotificationUnreadCountView.as_view(), name='notification-unread-count'),
]


# ==============================================================================
# ADMIN URL PATTERNS
# ==============================================================================

admin_patterns = [
    # Practitioner management
    path('practitioners/pending/', views.AdminPendingPractitionersView.as_view(), name='admin-pending'),
    path('practitioners/<int:pk>/approve/', views.AdminApprovePractitionerView.as_view(), name='admin-approve'),
    path('practitioners/<int:pk>/reject/', views.AdminRejectPractitionerView.as_view(), name='admin-reject'),
    
    # ========== ADMIN APPLICATION URLS ==========
    path('applications/', views.AdminApplicationListView.as_view(), name='admin-applications'),
    path('applications/<int:pk>/', views.AdminApplicationDetailView.as_view(), name='admin-application-detail'),
    path('applications/<int:pk>/action/', views.AdminApplicationActionView.as_view(), name='admin-application-action'),
]


# ==============================================================================
# MAIN URL PATTERNS
# ==============================================================================

urlpatterns = [
    # ========== ROOT & PUBLIC ==========
    path('', api_root, name='api-root'),
    path('health/', views.health_check, name='health-check'),
    
    # ========== AUTHENTICATION ==========
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.CurrentUserView.as_view(), name='current-user'),
    
    # ========== CORE RESOURCES ==========
    # Specialties
    path('specialties/', views.SpecialtyListView.as_view(), name='specialty-list'),
    
    # Practitioners (includes all practitioner patterns including applications)
    path('practitioners/', include(practitioner_patterns)),
    
    # Availability
    path('availability/', views.AvailabilityListCreateView.as_view(), name='availability-list'),
    path('availability/<int:pk>/', views.AvailabilityDetailView.as_view(), name='availability-detail'),
    
    # Consultations
    path('consultations/', include(consultation_patterns)),
    
    # Reviews
    path('reviews/', include(review_patterns)),
    
    # Notifications
    path('notifications/', include(notification_patterns)),
    
    # ========== ADMIN ==========
    path('admin/', include(admin_patterns)),
]


# ==============================================================================
# API DOCUMENTATION HELPER (Optional)
# ==============================================================================

@api_view(['GET'])
def api_docs(request):
    """API documentation endpoint"""
    base_url = request.build_absolute_uri('/').rstrip('/')
    
    docs = {
        "title": "NutriConnect API Documentation",
        "version": "2.0",
        "base_url": base_url,
        "sections": {
            "Authentication": {
                "Register": {"method": "POST", "url": "/register/", "description": "Create new account"},
                "Login": {"method": "POST", "url": "/login/", "description": "Login and get token"},
                "Logout": {"method": "POST", "url": "/logout/", "description": "Logout and invalidate token"},
                "Profile": {"method": "GET", "url": "/profile/", "description": "Get current user profile"},
            },
            "Practitioners": {
                "List Practitioners": {"method": "GET", "url": "/practitioners/", "description": "Get all verified practitioners"},
                "Practitioner Detail": {"method": "GET", "url": "/practitioners/{id}/", "description": "Get practitioner details"},
                "My Profile": {"method": "GET", "url": "/practitioners/me/", "description": "Get own practitioner profile"},
                "Update Profile": {"method": "PUT", "url": "/practitioners/me/", "description": "Update own profile"},
                "Create Application": {"method": "POST", "url": "/practitioners/application/create/", "description": "Create practitioner application"},
                "My Application": {"method": "GET", "url": "/practitioners/application/me/", "description": "Get your application"},
                "Submit Application": {"method": "POST", "url": "/practitioners/application/submit/", "description": "Submit for review"},
                "Application Status": {"method": "GET", "url": "/practitioners/application/status/", "description": "Check application status"},
            },
            "Consultations": {
                "List": {"method": "GET", "url": "/consultations/", "description": "Get your consultations"},
                "Create": {"method": "POST", "url": "/consultations/", "description": "Book consultation"},
                "Detail": {"method": "GET", "url": "/consultations/{id}/", "description": "Get consultation details"},
                "Update Status": {"method": "PATCH", "url": "/consultations/{id}/status/", "description": "Update consultation status"},
                "My Client": {"method": "GET", "url": "/consultations/my-client/", "description": "Client's consultations"},
                "My Practitioner": {"method": "GET", "url": "/consultations/my-practitioner/", "description": "Practitioner's consultations"},
                "Metrics": {"method": "GET", "url": "/consultations/metrics/", "description": "Dashboard metrics"},
            },
            "Reviews": {
                "Create": {"method": "POST", "url": "/reviews/create/", "description": "Write a review"},
                "My Reviews": {"method": "GET", "url": "/reviews/my-reviews/", "description": "Get your reviews"},
                "Practitioner Reviews": {"method": "GET", "url": "/practitioners/{id}/reviews/", "description": "Get practitioner's reviews"},
            },
            "Availability": {
                "List": {"method": "GET", "url": "/availability/", "description": "List availability"},
                "Create": {"method": "POST", "url": "/availability/", "description": "Create availability slot"},
                "Detail": {"method": "GET", "url": "/availability/{id}/", "description": "Get availability details"},
                "Update": {"method": "PUT", "url": "/availability/{id}/", "description": "Update availability"},
                "Delete": {"method": "DELETE", "url": "/availability/{id}/", "description": "Delete availability"},
                "Practitioner Public": {"method": "GET", "url": "/practitioners/{id}/availability/", "description": "Get practitioner's public availability"},
            },
            "Specialties": {
                "List": {"method": "GET", "url": "/specialties/", "description": "Get all specialties"},
            },
            "Notifications": {
                "List": {"method": "GET", "url": "/notifications/", "description": "Get notifications"},
                "Mark Read": {"method": "POST", "url": "/notifications/{id}/read/", "description": "Mark as read"},
                "Mark All Read": {"method": "POST", "url": "/notifications/mark-all-read/", "description": "Mark all as read"},
                "Unread Count": {"method": "GET", "url": "/notifications/unread-count/", "description": "Get unread count"},
            },
            "Admin": {
                "Pending Practitioners": {"method": "GET", "url": "/admin/practitioners/pending/", "description": "List unverified practitioners"},
                "Approve Practitioner": {"method": "PATCH", "url": "/admin/practitioners/{id}/approve/", "description": "Verify a practitioner"},
                "Reject Practitioner": {"method": "POST", "url": "/admin/practitioners/{id}/reject/", "description": "Reject a practitioner"},
                "List Applications": {"method": "GET", "url": "/admin/applications/", "description": "List all applications"},
                "Application Detail": {"method": "GET", "url": "/admin/applications/{id}/", "description": "View application details"},
                "Application Action": {"method": "POST", "url": "/admin/applications/{id}/action/", "description": "Approve/reject application"},
            }
        }
    }
    
    return JsonResponse(docs)