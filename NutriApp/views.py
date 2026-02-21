from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import User, Practitioner, Specialty, Availability, Consultation, Review
from .serializers import (
    RegisterSerializer, UserSerializer, PractitionerSerializer,
    SpecialtySerializer, AvailabilitySerializer, ConsultationSerializer,
    ReviewSerializer
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