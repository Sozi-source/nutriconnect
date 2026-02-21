from django.shortcuts import render
from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes 
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser, AllowAny
from .models import User, UserProfile, Specialty, Practitioner, Review, Availability, Consultation
from .serializers import (
    UserSerializer, ReviewSerializer, UserProfileSerializer, SpecialtySerializer, 
    ConsultationSerializer, PractitionerSerializer, AvailabilitySerializer,
    PractitionerDetailSerializer, BulkAvailabilitySerializer, TimeSlotSerializer,
    ConsultationCreateSerializer
)
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser, AllowAny
from .permissions import IsOwnerOrAdmin, IsConsultationClientOrAdmin, IsRelatedUserOwnerOrAdmin, IsAvailabilityOwnerOrAdmin, IsReviewOwnerOrAdmin, IsConsultationParticipantOrAdmin
from rest_framework.exceptions import ValidationError
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status, filters
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, F, Sum, Count
from .filters import PractitionerFilter
from datetime import datetime, timedelta, date
from django.utils import timezone
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework import permissions

# Create your views here.

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Public endpoint to check if API is running
    """
    return Response({
        'status': 'healthy',
        'message': 'NutriConnect API is running',
        'version': '1.0'
    })

class RegisterUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes =[AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # save the user
        user = serializer.save()

        # Refresh user instance to include profile
        user.refresh_from_db()

        # create token for the user
        token, created = Token.objects.get_or_create(user=user)
        # Return user data + token
        return Response({
            'user':UserSerializer(user).data,
            'token':token.key,
            'message':'Registration successful. You are now logged in.'
        }, status=status.HTTP_201_CREATED)

class ListUserView(generics.ListAPIView):
    queryset =User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset =User.objects.all()
    serializer_class = UserSerializer
    permission_classes =[IsAuthenticated, IsOwnerOrAdmin]
    

class CurrentUserView(generics.RetrieveAPIView):
    queryset =User.objects.all()
    serializer_class = UserSerializer
    permission_classes =[IsAuthenticated]

    def get_object(self):
        return self.request.user
    
class UserProfileCreateView(generics.CreateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class =UserProfileSerializer
    permission_classes = [IsAuthenticated]

class UserProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = UserProfile.objects.all()
    serializer_class =UserProfileSerializer
    permission_classes= [IsAuthenticated, IsOwnerOrAdmin]

class UserProfileListView(generics.ListAPIView):
    queryset = UserProfile.objects.all()
    serializer_class =UserProfileSerializer
    permission_classes =[IsAuthenticated]

class MyProfileView(generics.RetrieveAPIView):
    """Get the current user's profile"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        profile, created = UserProfile.objects.get_or_create(
            user=self.request.user,
            defaults={'role': 'client'}
        )
        return profile

class UserProfileUpdateView(generics.UpdateAPIView):
    """Update the current user's profile"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return get_object_or_404(UserProfile, user=self.request.user)

class SpecialtyListView(generics.ListAPIView):
    queryset = Specialty.objects.all()
    serializer_class = SpecialtySerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']

class SpecialtyDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Specialty.objects.all()
    serializer_class = SpecialtySerializer
    permission_classes =[IsAuthenticated, IsAdminUser]

class PractitionerListView(generics.ListAPIView):
    queryset = Practitioner.objects.filter(is_verified=True)
    serializer_class = PractitionerSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = PractitionerFilter

    filter_backends=[
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    search_fields = [
        'user__first_name',
        'user__last_name',
        'bio',
        'specialties__name',
        'city',
    ]

    ordering_fields = [
        'hourly_rate',
        'years_of_experience',
        'user__first_name',
    ]
    ordering = ['user__first_name'] #default


class PractitionerDetailView(generics.RetrieveAPIView):
    queryset = Practitioner.objects.all()
    serializer_class = PractitionerDetailSerializer
    permission_classes = [IsAuthenticated]

class PractitionerCreateView(generics.CreateAPIView):
    queryset = Practitioner.objects.all()
    serializer_class = PractitionerSerializer
    permission_classes = [IsAdminUser]

class PractitionerUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Practitioner.objects.all()
    serializer_class = PractitionerSerializer
    permission_classes = [IsAdminUser]

# ==================== ENHANCED AVAILABILITY VIEWS ====================

class IsPractitionerOwner(permissions.BasePermission):
    """Custom permission to only allow practitioners to edit their own availability"""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and hasattr(request.user, 'practitioner')
    
    def has_object_permission(self, request, view, obj):
        return obj.practitioner.user == request.user

class AvailabilityListCreateView(generics.ListCreateAPIView):
    """List and create availability slots for the logged-in practitioner"""
    serializer_class = AvailabilitySerializer
    permission_classes = [IsAuthenticated, IsPractitionerOwner]
    
    def get_queryset(self):
        practitioner = get_object_or_404(Practitioner, user=self.request.user)
        return Availability.objects.filter(practitioner=practitioner)
    
    def perform_create(self, serializer):
        practitioner = get_object_or_404(Practitioner, user=self.request.user)
        serializer.save(practitioner=practitioner)

class AvailabilityDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a specific availability slot"""
    serializer_class = AvailabilitySerializer
    permission_classes = [IsAuthenticated, IsPractitionerOwner]
    
    def get_queryset(self):
        practitioner = get_object_or_404(Practitioner, user=self.request.user)
        return Availability.objects.filter(practitioner=practitioner)

class BulkAvailabilityCreateView(APIView):
    """Create multiple weekly availability slots at once"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Ensure user has a practitioner profile
        if not hasattr(request.user, 'practitioner'):
            return Response(
                {'error': 'You must have a practitioner profile to set availability'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = BulkAvailabilitySerializer(data=request.data)
        if serializer.is_valid():
            created_slots = serializer.save()
            response_serializer = AvailabilitySerializer(created_slots, many=True)
            return Response({
                'message': f'Created {len(created_slots)} availability slots',
                'slots': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PractitionerAvailabilityView(generics.ListAPIView):
    """Public view to get availability for a specific practitioner"""
    serializer_class = AvailabilitySerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        practitioner_id = self.kwargs['practitioner_id']
        practitioner = get_object_or_404(Practitioner, id=practitioner_id, is_verified=True)
        
        # Return all available slots (is_available=True)
        return Availability.objects.filter(
            practitioner=practitioner,
            is_available=True
        )

class AvailableTimeSlotsView(APIView):
    """Get all available time slots for a practitioner within a date range"""
    permission_classes = [AllowAny]
    
    def get(self, request, practitioner_id):
        practitioner = get_object_or_404(Practitioner, id=practitioner_id, is_verified=True)
        
        # Get date range from query params
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            # Default to next 30 days
            start_date = timezone.now().date()
            end_date = start_date + timedelta(days=30)
        else:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Get all availability rules
        weekly_rules = Availability.objects.filter(
            practitioner=practitioner,
            recurrence_type='weekly',
            is_available=True
        )
        
        one_time_slots = Availability.objects.filter(
            practitioner=practitioner,
            recurrence_type='one_time',
            specific_date__range=[start_date, end_date],
            is_available=True
        )
        
        unavailable_blocks = Availability.objects.filter(
            practitioner=practitioner,
            recurrence_type='unavailable',
            specific_date__range=[start_date, end_date],
            is_available=False
        )
        
        # Generate all possible time slots
        available_slots = []
        current_date = start_date
        
        while current_date <= end_date:
            day_of_week = current_date.weekday()
            
            # Check if this date is in unavailable blocks
            is_unavailable = unavailable_blocks.filter(
                specific_date=current_date
            ).exists()
            
            if not is_unavailable:
                # Check weekly rules for this day
                day_rules = weekly_rules.filter(day_of_week=day_of_week)
                
                for rule in day_rules:
                    # Check if this specific time slot is already booked
                    is_booked = Consultation.objects.filter(
                        practitioner=practitioner,
                        date=current_date,
                        time=rule.start_time,
                        status__in=['booked', 'completed']
                    ).exists()
                    
                    if not is_booked:
                        available_slots.append({
                            'date': current_date,
                            'start_time': rule.start_time,
                            'end_time': rule.end_time,
                            'practitioner_id': practitioner.id,
                            'practitioner_name': practitioner.user.get_full_name()
                        })
                
                # Add one-time slots for this date
                for slot in one_time_slots.filter(specific_date=current_date):
                    is_booked = Consultation.objects.filter(
                        practitioner=practitioner,
                        date=current_date,
                        time=slot.start_time,
                        status__in=['booked', 'completed']
                    ).exists()
                    
                    if not is_booked:
                        available_slots.append({
                            'date': current_date,
                            'start_time': slot.start_time,
                            'end_time': slot.end_time,
                            'practitioner_id': practitioner.id,
                            'practitioner_name': practitioner.user.get_full_name()
                        })
            
            current_date += timedelta(days=1)
        
        serializer = TimeSlotSerializer(available_slots, many=True)
        return Response(serializer.data)

class CheckTimeSlotAvailabilityView(APIView):
    """Check if a specific time slot is available"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        practitioner_id = request.data.get('practitioner')
        booking_date = request.data.get('date')
        booking_time = request.data.get('time')
        
        if not all([practitioner_id, booking_date, booking_time]):
            return Response({
                'available': False,
                'error': 'Missing required fields (practitioner, date, time)'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            booking_date = datetime.strptime(booking_date, '%Y-%m-%d').date()
            booking_time = datetime.strptime(booking_time, '%H:%M:%S').time()
        except ValueError:
            return Response({
                'available': False,
                'error': 'Invalid date or time format. Use YYYY-MM-DD for date and HH:MM:SS for time'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        practitioner = get_object_or_404(Practitioner, id=practitioner_id)
        
        # Check if already booked
        if Consultation.objects.filter(
            practitioner=practitioner,
            date=booking_date,
            time=booking_time,
            status__in=['booked', 'completed']
        ).exists():
            return Response({
                'available': False,
                'reason': 'This time slot is already booked'
            })
        
        # Check if date is in the past
        booking_datetime = datetime.combine(booking_date, booking_time)
        if timezone.is_naive(booking_datetime):
            booking_datetime = timezone.make_aware(booking_datetime)
        
        if booking_datetime < timezone.now():
            return Response({
                'available': False,
                'reason': 'Cannot book appointments in the past'
            })
        
        # Use practitioner's availability method
        is_available = practitioner.is_available_at(booking_date, booking_time)
        
        if is_available:
            return Response({
                'available': True,
                'message': 'This time slot is available'
            })
        else:
            return Response({
                'available': False,
                'reason': 'Practitioner is not available at this time'
            })

class AvailabilityCreateView(generics.CreateAPIView):
    """Legacy view for backward compatibility"""
    queryset = Availability.objects.all()
    serializer_class = AvailabilitySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        practitioner = get_object_or_404(Practitioner, user=self.request.user)
        serializer.save(practitioner=practitioner)

class AvailabilityListView(generics.ListAPIView):
    serializer_class = AvailabilitySerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
    ]
    
    filterset_fields = {
        'day_of_week': ['exact', 'gte', 'lte'],
        'practitioner': ['exact'],
        'recurrence_type': ['exact'],
        'is_available': ['exact'],
    }
    
    ordering_fields = ['day_of_week', 'start_time', 'end_time', 'created_at']
    ordering = ['day_of_week', 'start_time']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Availability.objects.all()
        return Availability.objects.filter(practitioner__user=user)

# ==================== CONSULTATION VIEWS ====================

class ConsultationCreateView(generics.CreateAPIView):
    queryset = Consultation.objects.all()
    serializer_class = ConsultationCreateSerializer  
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)

class ConsultationListView(generics.ListAPIView):
    serializer_class = ConsultationSerializer
    permission_classes =[IsAuthenticated]

    filter_backends=[
        DjangoFilterBackend,
        filters.OrderingFilter
    ]

    filterset_fields = {
        'date': ['exact', 'gte', 'lte'],
        'status': ['exact'],
        'practitioner__user__email': ['exact'],
        'practitioner': ['exact'],
    }
    
    ordering_fields = ['date', 'time', 'created_at']
    ordering = ['-date', '-time']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Consultation.objects.all()
        return Consultation.objects.filter(
            Q(client=user) | Q(practitioner__user=user)
        ).select_related('client', 'practitioner__user')

class ConsultationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Consultation.objects.all()
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated, IsConsultationParticipantOrAdmin]
    
    def perform_destroy(self, instance):
        # Only allow cancellation, not hard delete
        instance.status = 'cancelled'
        instance.save()

class ConsultationStatusUpdateView(generics.UpdateAPIView):
    queryset = Consultation.objects.all()
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated, IsConsultationParticipantOrAdmin]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        
        # Only allow updating status
        new_status = request.data.get('status')
        if new_status not in ['completed', 'cancelled', 'no_show']:
            return Response(
                {'error': 'Invalid status. Allowed values: completed, cancelled, no_show'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        instance.status = new_status
        instance.save()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

class ConsultationMetricsView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Base filters
        client_filter = Q(client=user)
        practitioner_filter = Q(practitioner__user=user)
        
        # Add date range if provided
        if start_date and end_date:
            try:
                client_filter &= Q(date__range=[start_date, end_date])
                practitioner_filter &= Q(date__range=[start_date, end_date])
            except ValueError:
                return Response(
                    {'error': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Client metrics
        client_consultations = Consultation.objects.filter(client_filter)
        completed_client = client_consultations.filter(status='completed')
        
        # Practitioner metrics
        practitioner_consultations = Consultation.objects.filter(practitioner_filter)
        completed_practitioner = practitioner_consultations.filter(status='completed')
        
        # Calculate totals
        total_spent = completed_client.aggregate(
            total=Sum('practitioner__hourly_rate')
        )['total'] or 0
        
        total_earned = completed_practitioner.aggregate(
            total=Sum('practitioner__hourly_rate')
        )['total'] or 0
        
        # Format response
        return Response({
            'as_client': {
                'total_consultations': client_consultations.count(),
                'completed': completed_client.count(),
                'pending': client_consultations.filter(status='booked').count(),
                'cancelled': client_consultations.filter(status='cancelled').count(),
                'total_spent': float(total_spent),
            },
            'as_practitioner': {
                'total_consultations': practitioner_consultations.count(),
                'completed': completed_practitioner.count(),
                'pending': practitioner_consultations.filter(status='booked').count(),
                'cancelled': practitioner_consultations.filter(status='cancelled').count(),
                'total_earned': float(total_earned),
            }
        })
    
# ==================== REVIEW VIEWS ====================

class ReviewCreateView(generics.CreateAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        consultation = serializer.validated_data['consultation']
        if self.request.user != consultation.client and not self.request.user.is_staff:
            raise ValidationError("You can only review your own consultations.")
        if Review.objects.filter(consultation=consultation).exists():
            raise ValidationError("This consultation has already been reviewed.")
        serializer.save(reviewer=self.request.user)

class ReviewListView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
    ]
    
    filterset_fields = {
        'rating': ['exact', 'gte', 'lte'],
        'created_at': ['gte', 'lte'],
        'consultation__practitioner': ['exact'],
    }
    
    ordering_fields = ['rating', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Review.objects.all()
        return Review.objects.filter(
            Q(consultation__client=user) |
            Q(consultation__practitioner__user=user)
        ).select_related('consultation', 'reviewer')

class ReviewDetailView(generics.RetrieveAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, IsReviewOwnerOrAdmin]

class ReviewUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, IsReviewOwnerOrAdmin]


# ==================== AUTH VIEWS ====================

class LoginView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                'token': token.key,
                'user_id': user.pk,
                'email': user.email,
                'username': user.email,  # Use email as username since username field is None
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_practitioner': hasattr(user, 'practitioner'),
                'is_staff': user.is_staff,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': 'Invalid credentials',
                'detail': str(e)
            }, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(generics.GenericAPIView):
    permission_classes =[IsAuthenticated]

    def post(self, request):
        try:
            # Delete the token to force login again
            request.user.auth_token.delete()
            return Response({
                'message': 'Successfully logged out'
            }, status=status.HTTP_200_OK)
        except (AttributeError, Token.DoesNotExist):
            return Response({
                'error': 'Already logged out or token not found'
            }, status=status.HTTP_400_BAD_REQUEST)

# ==================== API ROOT VIEW ====================

@api_view(['GET'])
def api_root(request, format=None):
    """
    Welcome to the NutriConnect API.
    
    This is the root endpoint providing links to all available resources.
    """
    return Response({
        'message': 'Welcome to NutriConnect API',
        'version': '1.0',
        'documentation': 'For detailed docs, visit /swagger/ or /redoc/',
        
        # Authentication
        'authentication': {
            'register': reverse('register', request=request, format=format),
            'login': reverse('login', request=request, format=format),
            'logout': reverse('logout', request=request, format=format),
            'profile': reverse('current-user-profile', request=request, format=format),
        },
        
        # Users
        'users': {
            'list': reverse('user-list', request=request, format=format),
            'detail': '/users/{id}/',
        },
        
        # Profiles
        'profiles': {
            'my_profile': reverse('my-profile', request=request, format=format),
            'list': reverse('profile-list', request=request, format=format),
            'create': reverse('profile-create', request=request, format=format),
            'detail': '/profiles/{id}/',
        },
        
        # Specialties
        'specialties': {
            'list': reverse('specialty-list', request=request, format=format),
            'detail': '/specialties/{id}/',
        },
        
        # Practitioners
        'practitioners': {
            'list': reverse('practitioner-list', request=request, format=format),
            'create': reverse('practitioner-create', request=request, format=format),
            'detail': '/practitioners/{id}/',
            'update': '/practitioners/{id}/update/',
            'availability': '/practitioners/{practitioner_id}/availability/',
            'available_slots': '/practitioners/{practitioner_id}/available-slots/',
        },
        
        # Consultations
        'consultations': {
            'list': reverse('consultation-list', request=request, format=format),
            'create': reverse('consultation-create', request=request, format=format),
            'detail': '/consultations/{id}/',
            'status': '/consultations/{id}/status/',
            'reviews': '/consultations/{consultation_id}/reviews/',
        },
        
        # Availability
        'availability': {
            'list': reverse('availability-list', request=request, format=format),
            'create': reverse('availability-list-create', request=request, format=format),
            'bulk_create': reverse('availability-bulk-create', request=request, format=format),
            'check_slot': reverse('check-slot-availability', request=request, format=format),
            'detail': '/availability/{id}/',
        },

        # Metrics Dashboard
        'metrics': {
            'dashboard': reverse('consultation-metrics', request=request, format=format),
            'description': 'Get consultation statistics and summary metrics',
            'filters': '?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD',
        },
        
        # Reviews
        'reviews': {
            'list': reverse('review-list', request=request, format=format),
            'create': reverse('review-create', request=request, format=format),
            'detail': '/reviews/{id}/',
            'update': '/reviews/{id}/update/',
        },
    })

# ==================== DEBUG VIEW ====================

@api_view(['GET'])
@permission_classes([])  # Allow anyone for testing
def debug_auth(request):
    """Debug endpoint to check authentication"""
    auth_header = request.META.get('HTTP_AUTHORIZATION', 'No header')
    
    # Try to parse token
    token = None
    if auth_header.startswith('Token '):
        token = auth_header[6:]
    elif auth_header.startswith('token '):
        token = auth_header[6:]
    
    from rest_framework.authtoken.models import Token
    token_valid = False
    user_info = None
    
    if token:
        try:
            token_obj = Token.objects.get(key=token)
            token_valid = True
            user_info = {
                'id': token_obj.user.id,
                'email': token_obj.user.email,
                'first_name': token_obj.user.first_name,
                'last_name': token_obj.user.last_name,
            }
        except Token.DoesNotExist:
            token_valid = False
    
    return Response({
        'authenticated': request.user.is_authenticated,
        'user': str(request.user),
        'user_id': request.user.id if request.user.is_authenticated else None,
        'auth_header': auth_header,
        'token_provided': token is not None,
        'token_valid': token_valid,
        'user_info': user_info,
        'request_method': request.method,
        'request_path': request.path,
    })
