from django.urls import path, include
from django.http import JsonResponse
from . import views

# Root API endpoint with base URL
def api_root(request):
    base_url = request.build_absolute_uri('/').rstrip('/')
    
    return JsonResponse({
        "message": "Welcome to NutriConnect API",
        "version": "1.0",
        "base_url": base_url,
        "endpoints": {
            "Health Check": f"{base_url}/health/",
            "Register": f"{base_url}/register/",
            "Login": f"{base_url}/login/", 
            "Logout": f"{base_url}/logout/",
            "User Profile": f"{base_url}/profile/",
            "Specialties": f"{base_url}/specialties/",
            "Practitioners": f"{base_url}/practitioners/",
            "Availability": f"{base_url}/availability/",
            "Consultations": f"{base_url}/consultations/",
            "Admin - Pending": f"{base_url}/admin/practitioners/pending/",
            "Notifications": f"{base_url}/notifications/",
            "Notification Unread Count": f"{base_url}/notifications/unread-count/",
            "Admin - Approve": f"{base_url}/admin/practitioners/<id>/approve/"
        }
    })

# Practitioner URLs
practitioner_patterns = [
    path('', views.PractitionerListView.as_view(), name='practitioner-list'),
    path('<int:pk>/', views.PractitionerDetailView.as_view(), name='practitioner-detail'),
    path('me/', views.MyPractitionerProfileView.as_view(), name='practitioner-me'),
]

#Consultation URLS
consultation_patterns = [
    path('my-client/', views.MyClientConsultationsView.as_view()),
    path('my-practitioner/', views.MyPractitionerConsultationsView.as_view()),
    path('completed/no-review/', views.CompletedConsultationsNoReviewView.as_view()),
    path('metrics/', views.ConsultationMetricsView.as_view()),
]

#Notification URLS
notification_patterns =[
    path('', views.NotificationListView.as_view(), name='notification-list'),
    path('<int:pk>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    path('<int:pk>/read/', views.NotificationMarkReadView.as_view(), name='notification-mark-read'),
    path('mark-all-read/', views.NotificationMarkAllReadView.as_view(), name='notification-mark-all-read'),
    path('unread-count/', views.NotificationUnreadCountView.as_view(), name='notification-unread-count'),
]

# Main URL patterns
urlpatterns = [
    # Root
    path('', api_root, name='api-root'),
    path('health/', views.health_check, name='health-check'),
    
    # Auth
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.CurrentUserView.as_view(), name='current-user'),
    
    # Core resources
    path('specialties/', views.SpecialtyListView.as_view(), name='specialty-list'),
    path('practitioners/', include(practitioner_patterns)),
    path('availability/', views.AvailabilityListCreateView.as_view(), name='availability-list'),
    path('consultations/', include(consultation_patterns)),
    
    # Admin
    path('admin/practitioners/pending/', views.AdminPendingPractitionersView.as_view(), name='admin-pending'),
    path('admin/practitioners/<int:pk>/approve/', views.AdminApprovePractitionerView.as_view(), name='admin-approve'),

    #Notifications
    path('notifications/', include(notification_patterns)),

]
