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
from django.contrib.auth import authenticate, login
from rest_framework.authtoken.models import Token

# ==================== PUBLIC VIEWS ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({'status': 'healthy'})

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

# ==================== AUTH VIEWS ====================

class LoginView(APIView):
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
            
            return Response({
                'token': token.key,
                'user': {
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.profile.role if hasattr(user, 'profile') else 'client',
                }
            })
        else:
            return Response(
                {'error': 'Invalid email or password'},
                status=status.HTTP_401_UNAUTHORIZED
            )

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
    serializer_class = PractitionerSerializer
    permission_classes = [IsAuthenticated, IsClientOrAdmin]
    
    def get_queryset(self):
        return Practitioner.objects.filter(is_verified=True)

class PractitionerDetailView(generics.RetrieveAPIView):
    queryset = Practitioner.objects.filter(is_verified=True)
    serializer_class = PractitionerSerializer
    permission_classes = [IsAuthenticated, IsClientOrAdmin]

class MyPractitionerProfileView(generics.RetrieveAPIView):
    serializer_class = PractitionerSerializer
    permission_classes = [IsAuthenticated, IsPractitionerOrAdmin]
    
    def get_object(self):
        return get_object_or_404(Practitioner, user=self.request.user)

# ==================== ADMIN VIEWS ====================

class AdminPendingPractitionersView(generics.ListAPIView):
    serializer_class = PractitionerSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return Practitioner.objects.filter(is_verified=False)

class AdminApprovePractitionerView(generics.UpdateAPIView):
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
    queryset = Specialty.objects.all()
    serializer_class = SpecialtySerializer
    permission_classes = [IsAuthenticated]

# ==================== AVAILABILITY VIEWS ====================

class AvailabilityListCreateView(generics.ListCreateAPIView):
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
    serializer_class = AvailabilitySerializer
    permission_classes = [IsAuthenticated, IsPractitionerOrAdmin, CanManageOwnAvailability]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Availability.objects.all()
        return Availability.objects.filter(practitioner__user=self.request.user)

# ==================== CONSULTATION VIEWS ====================

class ConsultationListCreateView(generics.ListCreateAPIView):
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
        practitioner = serializer.validated_data.get('practitioner')
        if practitioner.user == self.request.user:
            raise PermissionError("Practitioners cannot book themselves")
        serializer.save(client=self.request.user)

class ConsultationDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated, CanManageOwnConsultations]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Consultation.objects.all()
        return Consultation.objects.filter(
            Q(client=self.request.user) | Q(practitioner__user=self.request.user)
        )

class MyClientConsultationsView(generics.ListAPIView):
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Consultation.objects.filter(client=self.request.user)
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('-date', '-time')

class MyPractitionerConsultationsView(generics.ListAPIView):
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated, IsPractitionerOrAdmin]

    def get_queryset(self):
        queryset = Consultation.objects.filter(practitioner__user=self.request.user)
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('-date', '-time')

class CompletedConsultationsNoReviewView(generics.ListAPIView):
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Consultation.objects.filter(
            client=self.request.user,
            status='completed',
            review__isnull=True
        ).order_by('-date', '-time')

class ConsultationMetricsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        if hasattr(user, 'practitioner'):
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

# ==================== NOTIFICATION VIEWS ====================

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

class NotificationDetailView(generics.RetrieveAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

class NotificationMarkReadView(APIView):
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
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        count = Notification.mark_all_as_read(request.user)
        return Response({'marked_read': count})

class NotificationUnreadCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
        return Response({'unread_count': count})