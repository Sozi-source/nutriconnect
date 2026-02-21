from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django.shortcuts import get_object_or_404
from .models import User, Practitioner, Specialty, Availability, Consultation, Review
from .serializers import (
    RegisterSerializer, UserSerializer, PractitionerSerializer,
    SpecialtySerializer, AvailabilitySerializer, ConsultationSerializer,
    ReviewSerializer
)
from . import models
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
    """Public list of verified practitioners"""
    serializer_class = PractitionerSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Practitioner.objects.filter(is_verified=True)

class PractitionerDetailView(generics.RetrieveAPIView):
    queryset = Practitioner.objects.all()
    serializer_class = PractitionerSerializer
    permission_classes = [IsAuthenticated]

class MyPractitionerProfileView(generics.RetrieveAPIView):
    """Get current user's practitioner profile"""
    serializer_class = PractitionerSerializer
    permission_classes = [IsAuthenticated]
    
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
    queryset = Specialty.objects.all()
    serializer_class = SpecialtySerializer
    permission_classes = [IsAuthenticated]

# ==================== AVAILABILITY VIEWS ====================

class AvailabilityListCreateView(generics.ListCreateAPIView):
    serializer_class = AvailabilitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Availability.objects.filter(practitioner__user=self.request.user)
    
    def perform_create(self, serializer):
        practitioner = get_object_or_404(Practitioner, user=self.request.user)
        serializer.save(practitioner=practitioner)

# ==================== CONSULTATION VIEWS ====================

class ConsultationListCreateView(generics.ListCreateAPIView):
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Consultation.objects.filter(
            models.Q(client=user) | models.Q(practitioner__user=user)
        )
    
    def perform_create(self, serializer):
        serializer.save(client=self.request.user)