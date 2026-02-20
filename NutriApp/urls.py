from django.urls import path, include
from . import views

# Practitioner nested URLs
practitioner_patterns = [
    # Practitioner CRUD
    path('', views.PractitionerListView.as_view(), name='practitioner-list'),
    path('create/', views.PractitionerCreateView.as_view(), name='practitioner-create'),
    path('<int:pk>/', views.PractitionerDetailView.as_view(), name='practitioner-detail'),
    path('<int:pk>/update/', views.PractitionerUpdateDeleteView.as_view(), name='practitioner-update'),
    
    # Nested availability under practitioner
    path('<int:practitioner_id>/availability/', include([
        path('', views.AvailabilityListView.as_view(), name='practitioner-availability-list'),
        path('create/', views.AvailabilityCreateView.as_view(), name='practitioner-availability-create'),
        path('<int:pk>/', views.AvailabilityDetailView.as_view(), name='practitioner-availability-detail'),
    ])),
    
    # Available slots for a practitioner (public)
    path('<int:practitioner_id>/available-slots/', 
         views.AvailableTimeSlotsView.as_view(), 
         name='practitioner-available-slots'),
]

# Consultation nested URLs
consultation_patterns = [
    # Consultation CRUD
    path('', views.ConsultationListView.as_view(), name='consultation-list'),
    path('create/', views.ConsultationCreateView.as_view(), name='consultation-create'),
    path('<int:pk>/', views.ConsultationDetailView.as_view(), name='consultation-detail'),
    path('<int:pk>/status/', views.ConsultationStatusUpdateView.as_view(), name='consultation-status'),
    
    # Nested reviews under consultation
    path('<int:consultation_id>/reviews/', include([
        path('', views.ReviewListView.as_view(), name='consultation-reviews'),
        path('create/', views.ReviewCreateView.as_view(), name='create-review'),
    ])),
]

# Main URL patterns
urlpatterns = [
    # Public health check 
    path('', views.health_check, name='health-check'),
    
    # Authentication & User Profile
    path('api/', views.api_root, name='api-root'),
    path('register/', views.RegisterUserView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.CurrentUserView.as_view(), name='current-user-profile'),
    
    # User Management (Admin only)
    path('users/', views.ListUserView.as_view(), name='user-list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    
    # User Profiles
    path('my-profile/', views.MyProfileView.as_view(), name='my-profile'),
    path('profiles/', views.UserProfileListView.as_view(), name='profile-list'),
    path('profiles/create/', views.UserProfileCreateView.as_view(), name='profile-create'),
    path('profiles/<int:pk>/', views.UserProfileDetailView.as_view(), name='profile-detail'),
    path('profiles/<int:pk>/update/', views.UserProfileUpdateView.as_view(), name='profile-update'),
    
    # Specialties
    path('specialties/', views.SpecialtyListView.as_view(), name='specialty-list'),
    path('specialties/<int:pk>/', views.SpecialtyDetailView.as_view(), name='specialty-detail'),
    
    # Practitioners (with nested availability)
    path('practitioners/', include(practitioner_patterns)),
    
    # Consultations (with nested reviews)
    path('consultations/', include(consultation_patterns)),
    
    # Standalone Availability (for practitioner's own availability management)
    path('availability/', views.AvailabilityListCreateView.as_view(), name='availability-list-create'),
    path('availability/<int:pk>/', views.AvailabilityDetailView.as_view(), name='availability-detail'),
    path('availability/bulk-create/', views.BulkAvailabilityCreateView.as_view(), name='availability-bulk-create'),
    
    # Check specific time slot availability
    path('availability/check-slot/', 
         views.CheckTimeSlotAvailabilityView.as_view(), 
         name='check-slot-availability'),
    
    # Standalone Reviews
    path('reviews/', views.ReviewListView.as_view(), name='review-list'),
    path('reviews/create/', views.ReviewCreateView.as_view(), name='review-create'),
    path('reviews/<int:pk>/', views.ReviewDetailView.as_view(), name='review-detail'),
    path('reviews/<int:pk>/update/', views.ReviewUpdateDeleteView.as_view(), name='review-update'),

    # Consultation Metrics
    path('metrics/', views.ConsultationMetricsView.as_view(), name='consultation-metrics'),
    
    # Debug endpoint
    path('api/debug-auth/', views.debug_auth, name='debug-auth'),
]