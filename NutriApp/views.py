from django.shortcuts import render
from rest_framework import generics
from .models import User, UserProfile, Specialty, Practitioner, Review, Availability, Consultation
from .serializers import UserSerializer, ReviewSerializer, UserProfileSerializer, SpecialtySerializer, ConsultationSerializer, PractitionerSerializer, AvailabilitySerializer
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser, AllowAny
from .permissions import IsOwnerOrAdmin, IsConsultationClientOrAdmin, IsRelatedUserOwnerOrAdmin, IsAvailabilityOwnerOrAdmin, IsReviewOwnerOrAdmin, IsConsultationParticipantOrAdmin
from rest_framework.exceptions import ValidationError
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status, filters
from rest_framework.decorators import api_view
from rest_framework.reverse import reverse
from django_filters.rest_framework import DjangoFilterBackend, OrderingFilter
from django.db.models import Q


# Create your views here.

class RegisterUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes =[AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # save the user
        user = serializer.save()
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
    permission_classes= [IsAuthenticated, IsRelatedUserOwnerOrAdmin]

class UserProfileListView(generics.ListAPIView):
    queryset = UserProfile.objects.all()
    serializer_class =UserProfileSerializer
    permission_classes =[IsAuthenticated, IsAdminUser]

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
    permission_classes =[IsAuthenticated]

class PractitionerListView(generics.ListAPIView):
    queryset = Practitioner.objects.all()
    serializer_class = PractitionerSerializer
    permission_classes = [IsAdminUser]

    filter_backends=[
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_fields= {
        'specialties__name': ['exact'],
        'city': ['exact'],
        'currency': ['exact'],
        'hourly_rate': ['lt', 'gt', 'range'],
        'experience_level': ['exact'],
        'is_verified': ['exact'],
    }

    search_fields = [
        'user__first_name',
        'user__last_name',
        'bio',
        'specialties__name',
        'city',
    ]

    ordering_fields = [
        'hourly_rate',
        'years_experience',
        'user__first_name',
    ]
    ordering = ['user__first_name'] #default


class PractitionerDetailView(generics.RetrieveAPIView):
    queryset = Practitioner.objects.all()
    serializer_class = PractitionerSerializer
    permission_classes = [IsAdminUser]

class PractitionerCreateView(generics.CreateAPIView):
    queryset = Practitioner.objects.all()
    serializer_class = PractitionerSerializer
    permission_classes = [IsAdminUser]

class PractitionerUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Practitioner.objects.all()
    serializer_class = PractitionerSerializer
    permission_classes = [IsAdminUser]

class AvailabilityCreateView(generics.CreateAPIView):
    queryset = Availability.objects.all()
    serializer_class = AvailabilitySerializer
    permission_classes = [IsAuthenticated]

class AvailabilityListView(generics.ListAPIView):
    serializer_class = AvailabilitySerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
    ]
    
    filterset_fields = {
        'date': ['exact', 'gte', 'lte'],
        'practitioner_id': ['exact'],
        'is_booked': ['exact'],
    }
    
    ordering_fields = ['date', 'time']
    ordering = ['date', 'time']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Availability.objects.all()
        return Availability.objects.filter(practitioner__user=user)


class AvailabilityDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Availability.objects.all()
    serializer_class = AvailabilitySerializer
    permission_classes = [IsAuthenticated, IsAvailabilityOwnerOrAdmin]

class ConsultationCreateView(generics.CreateAPIView):
    queryset = Consultation.objects.all()
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(client=self.request.user)

class ConsultationListView(generics.ListAPIView):
    serializer_class = ConsultationSerializer
    permission_classes =[IsAuthenticated]

    filter_backends=[
        DjangoFilterBackend,
        filter.OderingFilter
    ]

    filterset_fields = {
        'date': ['exact', 'gte', 'lte'],
        'status': ['exact'],
        'practitioner__user__email': ['exact'],
    }
    
    ordering_fields = ['date', 'time', 'created_at']
    ordering = ['-date', '-time']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Consultation.objects.all()
        return Consultation.objects.filter(client=user)|Consultation.objects.filter(practitioner__user=user)
       

class ConsultationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Consultation.objects.all()
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated, IsConsultationParticipantOrAdmin]
    

class ConsultationStatusUpdateView(generics.UpdateAPIView):
    queryset = Consultation.objects.all()
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated, IsConsultationParticipantOrAdmin]

class ReviewCreateView(generics.CreateAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, IsConsultationClientOrAdmin]

    def perform_create(self, serializer):
        consultation = serializer.validated_data['consultation']
        if self.request.user != consultation.client and not self.request.user.is_staff:
            raise PermissionError("You can only review your own consultations.")
        if Review.objects.filter(consultation=consultation).exists():
            raise ValidationError("This consultation has already been reviewed.")
        serializer.save(reviwer=self.request.user)

class ReviewListView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [
        DjangoFilterBackend,
        filters.OrderingFilter,
    ]
    
    filterset_fields = {
        'rating': ['exact', 'gte'],
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
            Q(consultation_client=user)|
            Q(consultation__practitioner__user=user)
            )

class ReviewDetailView(generics.RetrieveAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, IsReviewOwnerOrAdmin]

class ReviewUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, IsReviewOwnerOrAdmin]


# Auth Views
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
                'username': user.username,
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

# API ROOT VIEW
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
            'detail': '/availability/{id}/',
        },
        
        # Reviews
        'reviews': {
            'list': reverse('review-list', request=request, format=format),
            'create': reverse('review-create', request=request, format=format),
            'detail': '/reviews/{id}/',
            'update': '/reviews/{id}/update/',
        },
    })