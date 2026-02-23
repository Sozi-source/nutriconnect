from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.contrib.auth import authenticate, login
from django.utils import timezone

from .models import (
    User, Practitioner, Specialty, Availability, 
    Consultation, Review, Notification, PractitionerApplication
)
from .serializers import (
    # Auth serializers
    RegisterSerializer, UserSerializer,
    
    # Practitioner serializers
    PractitionerSerializer, PractitionerDetailSerializer,
    PractitionerApplicationSerializer, 
    PractitionerApplicationCreateSerializer,
    PractitionerApplicationUpdateSerializer,
    PractitionerApplicationReviewSerializer,
    
    # Specialty serializers
    SpecialtySerializer,
    
    # Availability serializers
    AvailabilitySerializer, AvailabilityCreateSerializer,
    
    # Consultation serializers
    ConsultationSerializer, ConsultationCreateSerializer,
    ConsultationUpdateSerializer,
    
    # Review serializers
    ReviewSerializer, ReviewCreateSerializer,
    
    # Notification serializers
    NotificationSerializer, NotificationMarkReadSerializer,
    
    # Dashboard serializers
    ClientDashboardStatsSerializer, PractitionerDashboardStatsSerializer
)
from .permissions import (
    IsClientUser, IsPractitionerUser, IsOwnerOrAdmin,
    IsClientOrAdmin, IsPractitionerOrAdmin, CanManageOwnAvailability,
    CanManageOwnConsultations, PreventSelfBooking, CanManageOwnApplication
)


# ==============================================================================
# HEALTH CHECK & PUBLIC UTILITIES
# ==============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Simple health check endpoint"""
    return Response({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat()
    })


# ==============================================================================
# AUTHENTICATION VIEWS
# ==============================================================================

class RegisterView(generics.CreateAPIView):
    """User registration endpoint - creates User, Profile, and optionally Practitioner"""
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class LoginView(APIView):
    """User login with email and password"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {'error': 'Please provide both email and password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            token, _ = Token.objects.get_or_create(user=user)
            
            # Get user role
            role = 'client'
            if hasattr(user, 'profile'):
                role = user.profile.role
            
            # Check for existing application
            has_application = hasattr(user, 'practitioner_application')
            application_status = None
            if has_application:
                application_status = user.practitioner_application.status
            
            return Response({
                'token': token.key,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': role,
                    'is_practitioner': hasattr(user, 'practitioner'),
                    'is_verified': hasattr(user, 'practitioner') and user.practitioner.is_verified,
                    'is_staff': user.is_staff,
                    'has_application': has_application,
                    'application_status': application_status,
                }
            })
        else:
            return Response(
                {'error': 'Invalid email or password'},
                status=status.HTTP_401_UNAUTHORIZED
            )


class LogoutView(generics.GenericAPIView):
    """User logout - deletes auth token"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        request.user.auth_token.delete()
        return Response({'message': 'Logged out successfully'})


# ==============================================================================
# USER PROFILE VIEWS
# ==============================================================================

class CurrentUserView(generics.RetrieveAPIView):
    """Get current authenticated user's profile"""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user


# ==============================================================================
# PRACTITIONER APPLICATION VIEWS
# ==============================================================================

class PractitionerApplicationCreateView(APIView):
    """Create a new practitioner application for EXISTING practitioner"""
    permission_classes = [IsAuthenticated, IsPractitionerUser]
    
    def post(self, request):
        # Check if user has practitioner profile
        if not hasattr(request.user, 'practitioner'):
            return Response(
                {'error': 'You must be registered as a practitioner first'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user already has an application
        if hasattr(request.user, 'practitioner_application'):
            return Response(
                {'error': 'You already have an application'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = PractitionerApplicationCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            application = serializer.save()
            return Response({
                'message': 'Application created successfully',
                'application_id': application.id,
                'status': 'draft'
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PractitionerApplicationDetailView(APIView):
    """Get user's practitioner application"""
    permission_classes = [IsAuthenticated, CanManageOwnApplication]
    
    def get(self, request):
        application = get_object_or_404(
            PractitionerApplication, 
            user=request.user
        )
        serializer = PractitionerApplicationSerializer(application)
        return Response(serializer.data)


class PractitionerApplicationUpdateView(APIView):
    """Update draft or info_needed application"""
    permission_classes = [IsAuthenticated, CanManageOwnApplication]
    
    def put(self, request):
        application = get_object_or_404(
            PractitionerApplication, 
            user=request.user,
            status__in=['draft', 'info_needed']
        )
        serializer = PractitionerApplicationUpdateSerializer(
            application, 
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Application updated',
                'status': application.status
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PractitionerApplicationSubmitView(APIView):
    """Submit application for review"""
    permission_classes = [IsAuthenticated, CanManageOwnApplication]
    
    def post(self, request):
        application = get_object_or_404(
            PractitionerApplication,
            user=request.user,
            status='draft'
        )
        
        # Validate required fields
        if not application.qualifications or not application.experience_description:
            return Response(
                {'error': 'Please complete all required fields'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        application.submit()
        return Response({
            'message': 'Application submitted for review',
            'status': 'pending'
        })


class PractitionerApplicationStatusView(APIView):
    """Check if user has an application and its status"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if hasattr(request.user, 'practitioner_application'):
            application = request.user.practitioner_application
            return Response({
                'has_application': True,
                'status': application.status,
                'application_id': application.id
            })
        return Response({
            'has_application': False
        })


# ==============================================================================
# PRACTITIONER PROFILE VIEWS
# ==============================================================================

class PractitionerListView(generics.ListAPIView):
    """List all verified practitioners"""
    serializer_class = PractitionerSerializer
    permission_classes = [IsAuthenticated, IsClientOrAdmin]
    
    def get_queryset(self):
        queryset = Practitioner.objects.filter(is_verified=True)
        
        # Apply filters from query params
        specialty = self.request.query_params.get('specialty')
        city = self.request.query_params.get('city')
        min_rate = self.request.query_params.get('min_rate')
        max_rate = self.request.query_params.get('max_rate')
        
        if specialty:
            queryset = queryset.filter(specialties__id=specialty)
        if city:
            queryset = queryset.filter(city__icontains=city)
        if min_rate:
            queryset = queryset.filter(hourly_rate__gte=min_rate)
        if max_rate:
            queryset = queryset.filter(hourly_rate__lte=max_rate)
        
        return queryset.distinct()


class PractitionerDetailView(generics.RetrieveAPIView):
    """View single practitioner details"""
    queryset = Practitioner.objects.filter(is_verified=True)
    serializer_class = PractitionerDetailSerializer
    permission_classes = [IsAuthenticated, IsClientOrAdmin]


class MyPractitionerProfileView(generics.RetrieveUpdateAPIView):
    """Get or update current user's practitioner profile"""
    serializer_class = PractitionerSerializer
    permission_classes = [IsAuthenticated, IsPractitionerOrAdmin]
    
    def get_object(self):
        return get_object_or_404(Practitioner, user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'message': 'Profile updated successfully',
            'profile': serializer.data
        })


# ==============================================================================
# SPECIALTY VIEWS
# ==============================================================================

class SpecialtyListView(generics.ListAPIView):
    """List all specialties"""
    queryset = Specialty.objects.all()
    serializer_class = SpecialtySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None


# ==============================================================================
# AVAILABILITY VIEWS
# ==============================================================================

class AvailabilityListCreateView(generics.ListCreateAPIView):
    """List and create availability slots"""
    permission_classes = [IsAuthenticated, IsPractitionerOrAdmin]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AvailabilityCreateSerializer
        return AvailabilitySerializer
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Availability.objects.all()
        return Availability.objects.filter(practitioner__user=self.request.user)
    
    def perform_create(self, serializer):
        practitioner = get_object_or_404(Practitioner, user=self.request.user)
        serializer.save(practitioner=practitioner)


class AvailabilityDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Manage individual availability slots"""
    serializer_class = AvailabilitySerializer
    permission_classes = [
        IsAuthenticated, 
        IsPractitionerOrAdmin, 
        CanManageOwnAvailability
    ]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Availability.objects.all()
        return Availability.objects.filter(practitioner__user=self.request.user)


class PractitionerAvailabilityView(generics.ListAPIView):
    """Get availability for a specific practitioner (public)"""
    serializer_class = AvailabilitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        practitioner_id = self.kwargs.get('pk')
        return Availability.objects.filter(
            practitioner_id=practitioner_id,
            is_available=True
        )


# ==============================================================================
# CONSULTATION VIEWS
# ==============================================================================

class ConsultationListCreateView(generics.ListCreateAPIView):
    """List and create consultations"""
    permission_classes = [IsAuthenticated, PreventSelfBooking]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ConsultationCreateSerializer
        return ConsultationSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Consultation.objects.all()
        return Consultation.objects.filter(
            Q(client=user) | Q(practitioner__user=user)
        )
    
    def perform_create(self, serializer):
        practitioner = serializer.validated_data.get('practitioner')
        if practitioner.user == self.request.user:
            raise PermissionError("Practitioners cannot book themselves")
        serializer.save(client=self.request.user)


class ConsultationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Manage individual consultations"""
    permission_classes = [IsAuthenticated, CanManageOwnConsultations]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ConsultationUpdateSerializer
        return ConsultationSerializer
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Consultation.objects.all()
        return Consultation.objects.filter(
            Q(client=self.request.user) | Q(practitioner__user=self.request.user)
        )


class MyClientConsultationsView(generics.ListAPIView):
    """Get current client's consultations"""
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Consultation.objects.filter(client=self.request.user)
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('-date', '-time')


class MyPractitionerConsultationsView(generics.ListAPIView):
    """Get current practitioner's consultations"""
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated, IsPractitionerOrAdmin]

    def get_queryset(self):
        queryset = Consultation.objects.filter(practitioner__user=self.request.user)
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('-date', '-time')


class ConsultationUpdateStatusView(APIView):
    """Update consultation status"""
    permission_classes = [IsAuthenticated, CanManageOwnConsultations]
    
    def patch(self, request, pk):
        consultation = get_object_or_404(Consultation, pk=pk)
        new_status = request.data.get('status')
        
        if new_status not in ['completed', 'cancelled']:
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        consultation.status = new_status
        consultation.save()
        
        # Create notification
        Notification.objects.create(
            recipient=consultation.client if new_status == 'completed' else consultation.practitioner.user,
            notification_type='CONSULTATION_COMPLETED' if new_status == 'completed' else 'CONSULTATION_CANCELLED',
            title=f'Consultation {new_status}',
            message=f'Your consultation has been marked as {new_status}',
            data={'consultation_id': consultation.id}
        )
        
        return Response({'message': f'Consultation marked as {new_status}'})


class CompletedConsultationsNoReviewView(generics.ListAPIView):
    """Get completed consultations without reviews"""
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Consultation.objects.filter(
            client=self.request.user,
            status='completed',
            review__isnull=True
        ).order_by('-date', '-time')


# ==============================================================================
# REVIEW VIEWS
# ==============================================================================

class ReviewCreateView(APIView):
    """Create a review for a completed consultation"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ReviewCreateSerializer(data=request.data)
        if serializer.is_valid():
            review = serializer.save(reviewer=request.user)
            
            # Create notification for practitioner
            Notification.objects.create(
                recipient=review.consultation.practitioner.user,
                notification_type='REVIEW_RECEIVED',
                title='New Review Received',
                message=f'You received a {review.rating}-star review',
                data={
                    'review_id': review.id,
                    'consultation_id': review.consultation.id
                }
            )
            
            return Response({
                'message': 'Review submitted successfully',
                'review': ReviewSerializer(review).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MyReviewsView(generics.ListAPIView):
    """Get reviews written by current user"""
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Review.objects.filter(reviewer=self.request.user)


class PractitionerReviewsView(generics.ListAPIView):
    """Get reviews for a practitioner"""
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        practitioner_id = self.kwargs.get('pk')
        return Review.objects.filter(
            consultation__practitioner_id=practitioner_id
        )


# ==============================================================================
# NOTIFICATION VIEWS
# ==============================================================================

class NotificationListView(generics.ListAPIView):
    """Get all notifications for current user"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class NotificationDetailView(generics.RetrieveAPIView):
    """Get a specific notification"""
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)


class NotificationMarkReadView(APIView):
    """Mark a notification as read"""
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
    """Mark all notifications as read"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        count = Notification.mark_all_as_read(request.user)
        return Response({
            'message': f'Marked {count} notifications as read',
            'count': count
        })


class NotificationUnreadCountView(APIView):
    """Get count of unread notifications"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        return Response({'unread_count': count})


# ==============================================================================
# DASHBOARD METRICS VIEWS
# ==============================================================================

class ConsultationMetricsView(APIView):
    """Get dashboard statistics"""
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
                'total_earnings': sum(float(c.practitioner.hourly_rate or 0) for c in completed),
                'average_rating': 0,  # Calculate from reviews
            }
            
            serializer = PractitionerDashboardStatsSerializer(metrics)
            
        else:
            # Client metrics
            consultations = Consultation.objects.filter(client=user)
            completed = consultations.filter(status='completed')
            
            metrics = {
                'total_consultations': consultations.count(),
                'completed_consultations': completed.count(),
                'upcoming_consultations': consultations.filter(status='booked').count(),
                'cancelled_consultations': consultations.filter(status='cancelled').count(),
                'total_spent': sum(float(c.practitioner.hourly_rate or 0) for c in completed),
                'pending_reviews': consultations.filter(status='completed', review__isnull=True).count(),
            }
            
            serializer = ClientDashboardStatsSerializer(metrics)
        
        return Response(serializer.data)


# ==============================================================================
# ADMIN VIEWS
# ==============================================================================

class AdminPendingPractitionersView(generics.ListAPIView):
    """Admin: View all unverified practitioners"""
    serializer_class = PractitionerSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return Practitioner.objects.filter(is_verified=False)


class AdminApprovePractitionerView(generics.UpdateAPIView):
    """Admin: Approve a practitioner (direct approval without application)"""
    queryset = Practitioner.objects.all()
    serializer_class = PractitionerSerializer
    permission_classes = [IsAdminUser]
    
    def update(self, request, *args, **kwargs):
        practitioner = self.get_object()
        practitioner.is_verified = True
        practitioner.save()
        
        # Send notification
        Notification.objects.create(
            recipient=practitioner.user,
            notification_type='PRACTITIONER_VERIFIED',
            title='Account Verified',
            message='Your practitioner account has been verified! You can now accept bookings.'
        )
        
        return Response({'message': 'Practitioner approved successfully'})


class AdminApplicationListView(generics.ListAPIView):
    """Admin: List all practitioner applications"""
    serializer_class = PractitionerApplicationSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        status = self.request.query_params.get('status', 'pending')
        return PractitionerApplication.objects.filter(status=status)


class AdminApplicationDetailView(APIView):
    """Admin: Review and process applications"""
    permission_classes = [IsAdminUser]
    
    def get(self, request, pk):
        application = get_object_or_404(PractitionerApplication, pk=pk)
        serializer = PractitionerApplicationReviewSerializer(application)
        return Response(serializer.data)
    
    def post(self, request, pk):
        application = get_object_or_404(PractitionerApplication, pk=pk)
        action = request.data.get('action')
        
        if action == 'approve':
            application.approve(request.user)
            return Response({'message': 'Application approved', 'status': 'approved'})
        
        elif action == 'reject':
            reason = request.data.get('reason', 'No reason provided')
            application.reject(request.user, reason)
            return Response({'message': 'Application rejected', 'status': 'rejected'})
        
        elif action == 'request_info':
            notes = request.data.get('notes', '')
            application.request_more_info(request.user, notes)
            return Response({'message': 'More information requested', 'status': 'info_needed'})
        
        return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)