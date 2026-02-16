from django.shortcuts import render
from rest_framework import generics
from .models import User, UserProfile, Specialty, Practitioner, Review, Availability, Consultation
from .serializers import UserSerializer, UserProfileSerializer, SpecialtySerializer, PractitionerSerializer
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, IsAdminUser

# Create your views here.

class RegisterUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class ListUserView(generics.ListAPIView):
    queryset =User.objects.all()
    serializer_class = UserSerializer

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset =User.objects.all()
    serializer_class = UserSerializer

class CurrentUserView(generics.RetrieveAPIView):
    queryset =User.objects.all()
    serializer_class = UserSerializer
    permission_classes =[IsAuthenticated]

    def get_object(self):
        return self.request.user
    
class UserProfileCreateView(generics.CreateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class =UserProfileSerializer

class UserProfileDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = UserProfile.objects.all()
    serializer_class =UserProfileSerializer
    permission_classes= [IsAuthenticated]

class UserProfileListView(generics.ListAPIView):
    queryset = UserProfile.objects.all()
    serializer_class =UserProfileSerializer
    permission_classes =[IsAdminUser]

class SpecialtyListView(generics.ListAPIView):
    queryset = Specialty.objects.all()
    serializer_class = SpecialtySerializer

class SpecialtyDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Specialty.objects.all()
    serializer_class = SpecialtySerializer

class PractitionerListView(generics.ListAPIView):
    queryset = Practitioner
    serializer_class = PractitionerSerializer

class PractitionerDetailView(generics.RetrieveAPIView):
    queryset = Practitioner
    serializer_class = PractitionerSerializer

class PractitionerCreateView(generics.CreateAPIView):
    queryset = Practitioner
    serializer_class = PractitionerSerializer

class PractitionerUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Practitioner
    serializer_class = PractitionerSerializer