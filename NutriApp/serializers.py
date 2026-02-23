from rest_framework import serializers
from .models import User, UserProfile, Specialty, Practitioner, Availability, Consultation, Review, Notification
from django.db import transaction

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'role', 'phone']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=['client', 'practitioner'], write_only=True)
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    # Practitioner fields
    bio = serializers.CharField(write_only=True, required=False, allow_blank=True)
    city = serializers.CharField(write_only=True, required=False, allow_blank=True)
    hourly_rate = serializers.DecimalField(max_digits=10, decimal_places=2, write_only=True, required=False)
    years_of_experience = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'password',
            'role', 'phone', 'bio', 'city', 'hourly_rate', 'years_of_experience'
        ]

    def create(self, validated_data):
        role = validated_data.pop('role')
        phone = validated_data.pop('phone', '')
        
        bio = validated_data.pop('bio', '')
        city = validated_data.pop('city', '')
        hourly_rate = validated_data.pop('hourly_rate', 0.00)
        years_of_experience = validated_data.pop('years_of_experience', 0)

        with transaction.atomic():
            user = User.objects.create_user(**validated_data)
            
            UserProfile.objects.create(
                user=user,
                role=role,
                phone=phone
            )
            
            if role == 'practitioner':
                Practitioner.objects.create(
                    user=user,
                    bio=bio,
                    city=city,
                    hourly_rate=hourly_rate,
                    years_of_experience=years_of_experience,
                    currency='KES',
                    is_verified=False,  # Needs admin approval
                    profile_complete=False
                )
            
            return user

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'profile']

class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ['id', 'name', 'description']

class PractitionerSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    full_name = serializers.SerializerMethodField()
    specialties = SpecialtySerializer(many=True, read_only=True)

    class Meta:
        model = Practitioner
        fields = [
            'id', 'user', 'first_name', 'last_name', 'full_name', 'email',
            'bio', 'city', 'hourly_rate', 'currency', 'years_of_experience',
            'is_verified', 'profile_complete', 'specialties', 'created_at'
        ]
        read_only_fields = ['created_at', 'is_verified']

    def get_full_name(self, obj):
        return obj.user.get_full_name()

class AvailabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Availability
        fields = '__all__'

class ConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultation
        fields = '__all__'

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'


#====================================================================================================
# NOTIFICATION SERIALIZER
#====================================================================================================
class NotificationSerializer(serializers.ModelSerializer):
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'message', 
            'data', 'is_read', 'created_at', 'read_at', 'time_ago'
        ]
        read_only_fields = ['id', 'created_at', 'read_at']
    
    def get_time_ago(self, obj):
        from django.utils.timesince import timesince
        return timesince(obj.created_at)