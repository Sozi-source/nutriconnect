from django.urls import path, include
from . import views

# Authentication urls

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
    # Authentication & User Profile
    path('register/', views.RegisterUserView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('profile/', views.CurrentUserView.as_view(), name='profile'),  # Current authenticated user
    
    # User Management (Admin only)
    path('users/', views.ListUserView.as_view(), name='user-list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    
    # User Profiles
    path('profiles/', views.UserProfileListView.as_view(), name='profile-list'),
    path('profiles/create/', views.UserProfileCreateView.as_view(), name='profile-create'),
    path('profiles/<int:pk>/', views.UserProfileDetailView.as_view(), name='profile-detail'),
    
    # Specialties
    path('specialties/', views.SpecialtyListView.as_view(), name='specialty-list'),
    path('specialties/<int:pk>/', views.SpecialtyDetailView.as_view(), name='specialty-detail'),
    
    # Practitioners (with nested availability)
    path('practitioners/', include(practitioner_patterns)),
    
    # Consultations (with nested reviews)
    path('consultations/', include(consultation_patterns)),
    
    # Standalone Availability (for listing all availability)
    path('availability/', views.AvailabilityListView.as_view(), name='availability-list'),
    path('availability/<int:pk>/', views.AvailabilityDetailView.as_view(), name='availability-detail'),
    
    # Standalone Reviews
    path('reviews/', views.ReviewListView.as_view(), name='review-list'),
    path('reviews/create/', views.ReviewCreateView.as_view(), name='review-create'),
    path('reviews/<int:pk>/', views.ReviewDetailView.as_view(), name='review-detail'),
    path('reviews/<int:pk>/update/', views.ReviewUpdateDeleteView.as_view(), name='review-update'),
]



