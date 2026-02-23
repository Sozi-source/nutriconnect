from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import User, Practitioner, Specialty, Availability, Consultation, Review, Notification
from rest_framework.views import APIView
from .serializers import (
    RegisterSerializer, UserSerializer, PractitionerSerializer,
    SpecialtySerializer, AvailabilitySerializer, ConsultationSerializer,
    ReviewSerializer, NotificationSerializer
)
from .permissions import (
    IsClientUser, IsPractitionerUser, IsOwnerOrAdmin,
    IsClientOrAdmin, IsPractitionerOrAdmin, CanManageOwnAvailability,
    CanManageOwnConsultations, PreventSelfBooking
)

# ==================== PUBLIC VIEWS ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({'status': 'healthy'})

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

# ==================== AUTH VIEWS ====================

from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token

class LoginView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.profile.role if hasattr(user, 'profile') else 'client',
            'is_practitioner': hasattr(user, 'practitioner'),
            'is_verified': hasattr(user, 'practitioner') and user.practitioner.is_verified,
            'is_staff': user.is_staff,
        })

class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        request.user.auth_token.delete()
        return Response({'message': 'Logged out successfully'})

# ==================== USER VIEWS ====================

class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user

# ==================== PRACTITIONER VIEWS ====================

class PractitionerListView(generics.ListAPIView):
    """
    List all verified practitioners.
    Accessible by: Clients and Admins only
    Practitioners cannot view the list (to prevent self-booking)
    """
    serializer_class = PractitionerSerializer
    permission_classes = [IsAuthenticated, IsClientOrAdmin]
    
    def get_queryset(self):
        return Practitioner.objects.filter(is_verified=True)

class PractitionerDetailView(generics.RetrieveAPIView):
    """
    View single practitioner details.
    Accessible by: Clients and Admins only
    """
    queryset = Practitioner.objects.filter(is_verified=True)
    serializer_class = PractitionerSerializer
    permission_classes = [IsAuthenticated, IsClientOrAdmin]

class MyPractitionerProfileView(generics.RetrieveAPIView):
    """
    Get current user's practitioner profile.
    Accessible by: Practitioners only
    """
    serializer_class = PractitionerSerializer
    permission_classes = [IsAuthenticated, IsPractitionerOrAdmin]
    
    def get_object(self):
        return get_object_or_404(Practitioner, user=self.request.user)

# ==================== ADMIN VIEWS ====================

class AdminPendingPractitionersView(generics.ListAPIView):
    """Admin view - see all unverified practitioners"""
    serializer_class = PractitionerSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return Practitioner.objects.filter(is_verified=False)

class AdminApprovePractitionerView(generics.UpdateAPIView):
    """Admin approves a practitioner"""
    queryset = Practitioner.objects.all()
    serializer_class = PractitionerSerializer
    permission_classes = [IsAdminUser]
    
    def update(self, request, *args, **kwargs):
        practitioner = self.get_object()
        practitioner.is_verified = True
        practitioner.save()
        return Response({'message': 'Practitioner approved successfully'})

# ==================== SPECIALTY VIEWS ====================

class SpecialtyListView(generics.ListAPIView):
    """
    List all specialties.
    Accessible by: All authenticated users
    """
    queryset = Specialty.objects.all()
    serializer_class = SpecialtySerializer
    permission_classes = [IsAuthenticated]

# ==================== AVAILABILITY VIEWS ====================

class AvailabilityListCreateView(generics.ListCreateAPIView):
    """
    List and create availability slots.
    Practitioners can only see/create their own.
    Clients cannot access.
    """
    serializer_class = AvailabilitySerializer
    permission_classes = [IsAuthenticated, IsPractitionerOrAdmin]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Availability.objects.all()
        return Availability.objects.filter(practitioner__user=self.request.user)
    
    def perform_create(self, serializer):
        practitioner = get_object_or_404(Practitioner, user=self.request.user)
        serializer.save(practitioner=practitioner)

class AvailabilityDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete an availability slot.
    Practitioners can only manage their own.
    """
    serializer_class = AvailabilitySerializer
    permission_classes = [IsAuthenticated, IsPractitionerOrAdmin, CanManageOwnAvailability]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Availability.objects.all()
        return Availability.objects.filter(practitioner__user=self.request.user)

# ==================== CONSULTATION VIEWS ====================

class ConsultationListCreateView(generics.ListCreateAPIView):
    """
    List and create consultations.
    - Clients see their own consultations
    - Practitioners see their own consultations
    - Admins see all
    - Prevents practitioners from booking themselves
    """
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated, PreventSelfBooking]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Consultation.objects.all()
        return Consultation.objects.filter(
            Q(client=user) | Q(practitioner__user=user)
        )
    
    def perform_create(self, serializer):
        # Check if practitioner is trying to book themselves
        practitioner = serializer.validated_data.get('practitioner')
        if practitioner.user == self.request.user:
            raise PermissionError("Practitioners cannot book themselves")
        serializer.save(client=self.request.user)

class ConsultationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a consultation.
    Users can only access their own consultations.
    """
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated, CanManageOwnConsultations]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Consultation.objects.all()
        return Consultation.objects.filter(
            Q(client=self.request.user) | Q(practitioner__user=self.request.user)
        )

# ==============================================================================
# CLIENT CONSULTATIONS (For client dashboard)
# ==============================================================================

class MyClientConsultationsView(generics.ListAPIView):
    """GET /consultations/my-client/ - Shows client's consultations"""
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Consultation.objects.filter(client=self.request.user)
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('-date', '-time')


# ==============================================================================
# PRACTITIONER CONSULTATIONS (For practitioner dashboard)
# ==============================================================================

class MyPractitionerConsultationsView(generics.ListAPIView):
    """GET /consultations/my-practitioner/ - Shows practitioner's consultations"""
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated, IsPractitionerOrAdmin]

    def get_queryset(self):
        queryset = Consultation.objects.filter(practitioner__user=self.request.user)
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('-date', '-time')


# ==============================================================================
# COMPLETED CONSULTATIONS WITHOUT REVIEWS (For review feature)
# ==============================================================================

class CompletedConsultationsNoReviewView(generics.ListAPIView):
    """GET /consultations/completed/no-review/ - Consultations ready for review"""
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Consultation.objects.filter(
            client=self.request.user,
            status='completed',
            review__isnull=True
        ).order_by('-date', '-time')


# ==============================================================================
# DASHBOARD METRICS (For statistics cards)
# ==============================================================================

class ConsultationMetricsView(APIView):
    """GET /consultations/metrics/ - Dashboard statistics"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        if hasattr(user, 'practitioner'):
            # Practitioner metrics
            consultations = Consultation.objects.filter(practitioner__user=user)
            completed = consultations.filter(status='completed')
            
            metrics = {
                'total_consultations': consultations.count(),
                'completed_consultations': completed.count(),
                'upcoming_consultations': consultations.filter(status='booked').count(),
                'cancelled_consultations': consultations.filter(status='cancelled').count(),
                'total_earnings': sum(c.price or 500 for c in completed),
            }
        else:
            # Client metrics
            consultations = Consultation.objects.filter(client=user)
            completed = consultations.filter(status='completed')
            
            metrics = {
                'total_consultations': consultations.count(),
                'completed_consultations': completed.count(),
                'upcoming_consultations': consultations.filter(status='booked').count(),
                'cancelled_consultations': consultations.filter(status='cancelled').count(),
                'total_spent': sum(c.price or 500 for c in completed),
                'pending_reviews': consultations.filter(status='completed', review__isnull=True).count(),
            }
        
        return Response(metrics)
    

    #================================================================================================
    # NOTIFICATION VIEWS
    #================================================================================================

class NotificationListView(generics.ListAPIView):
    """
    GET /notifications/
    Returns all notifications for the current user
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class NotificationDetailView(generics.RetrieveAPIView):
    """
    GET /notifications/{id}/
    Returns a specific notification
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class NotificationMarkReadView(APIView):
    """
    POST /notifications/{id}/read/
    Mark a specific notification as read
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        notification = get_object_or_404(
            Notification, 
            pk=pk, 
            recipient=request.user
        )
        notification.mark_as_read()
        return Response({'status': 'marked as read'})


class NotificationMarkAllReadView(APIView):
    """
    POST /notifications/mark-all-read/
    Mark all user's notifications as read
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        count = Notification.mark_all_as_read(request.user)
        return Response({'marked_read': count})


class NotificationUnreadCountView(APIView):
    """
    GET /notifications/unread-count/
    Returns count of unread notifications
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        return Response({'unread_count': count})