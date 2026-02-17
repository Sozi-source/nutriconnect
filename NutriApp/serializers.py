from rest_framework import serializers
from .models import User, UserProfile, Specialty, Consultation, Availability, Review, Practitioner


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'role', 'phone']

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    profile = UserProfileSerializer(read_only=True)

    role = serializers.ChoiceField(
        choices=['client', 'practitioner'],
        write_only = True,
        required = False,
        default = 'client'
    )
    phone = serializers.CharField(
        write_only=True, 
        required=False, 
        allow_blank=True,
        default=''
    )
    
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'password', 'profile', 'role', 'phone']
    
    def create(self, validated_data):
        role = validated_data.pop('role', 'client')
        phone =validated_data.pop('phone')

        # create user
        user = User.objects.create_user(**validated_data)

        # Update or create profile
        if hasattr(user, 'profile'):
            profile = user.profile
            profile.role =role
            profile.phone = phone
            profile.save()
        else:
            UserProfile.objects.create(user=user, role=role, phone=phone)
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
