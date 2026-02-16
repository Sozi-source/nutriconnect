from rest_framework import serializers
from .models import User, UserProfile, Specialty, Consultation, Availability, Review, Practitioner


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'role', 'phone']

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id','email', 'password', 'profile']
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ['id', 'name', 'description']

class ConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model =Consultation
        fields = ['id', 'client', 'practitioner', 'date', 'time', 'status']

class AvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Availability
        fields = ['id', 'practitioner', 'day_of_week', 'start_time', 'end_time']

class PractitionerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Practitioner
        fields = ['id', 'user', 'bio', 'currency','hourly_rate', 'specialties']

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'consultation', 'rating', 'comment', 'created_at']
        read_only_fields = ['created_at']
