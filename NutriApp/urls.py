from django.urls import path, include
from . import views

urlpatterns = [
    # Public
    path('health/', views.health_check, name='health-check'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # User
    path('profile/', views.CurrentUserView.as_view(), name='current-user'),
    
    # Specialties
    path('specialties/', views.SpecialtyListView.as_view(), name='specialty-list'),
    
    # Practitioners (public - only verified)
    path('practitioners/', views.PractitionerListView.as_view(), name='practitioner-list'),
    path('practitioners/<int:pk>/', views.PractitionerDetailView.as_view(), name='practitioner-detail'),
    path('practitioners/me/', views.MyPractitionerProfileView.as_view(), name='my-practitioner'),
    
    # Admin
    path('admin/practitioners/pending/', views.AdminPendingPractitionersView.as_view(), name='admin-pending'),
    path('admin/practitioners/<int:pk>/approve/', views.AdminApprovePractitionerView.as_view(), name='admin-approve'),
    
    # Availability
    path('availability/', views.AvailabilityListCreateView.as_view(), name='availability-list'),
    
    # Consultations
    path('consultations/', views.ConsultationListCreateView.as_view(), name='consultation-list'),
]