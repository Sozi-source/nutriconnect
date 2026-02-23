from rest_framework import serializers
from .models import (
    User, UserProfile, Specialty, Practitioner, 
    Availability, Consultation, Review, Notification,
    PractitionerApplication
)
from django.db import transaction

# ==============================================================================
# PROFILE SERIALIZERS
# ==============================================================================

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'role', 'phone']

# ==============================================================================
# USER SERIALIZERS
# ==============================================================================

class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'profile']

# ==============================================================================
# AUTHENTICATION SERIALIZERS
# ==============================================================================

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=['client', 'practitioner'], write_only=True)
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    bio = serializers.CharField(write_only=True, required=False, allow_blank=True)
    city = serializers.CharField(write_only=True, required=False, allow_blank=True)
    hourly_rate = serializers.DecimalField(
        max_digits=10, decimal_places=2, 
        write_only=True, required=False, allow_null=True
    )
    years_of_experience = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'password',
            'role', 'phone', 'bio', 'city', 'hourly_rate', 
            'years_of_experience'
        ]

    def _create_user(self, validated_data):
        return User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
    
    def _create_profile(self, user, role, phone):
        return UserProfile.objects.create(
            user=user,
            role=role,
            phone=phone
        )
    
    def _create_practitioner(self, user, practitioner_data):
        return Practitioner.objects.create(
            user=user,
            bio=practitioner_data.get('bio', ''),
            city=practitioner_data.get('city', ''),
            hourly_rate=practitioner_data.get('hourly_rate') or 0.00,
            years_of_experience=practitioner_data.get('years_of_experience') or 0,
            currency='KES',
            is_verified=False,
            profile_complete=False
        )
    
    def create(self, validated_data):
        role = validated_data.pop('role')
        phone = validated_data.pop('phone', '')
        
        practitioner_data = {
            'bio': validated_data.pop('bio', ''),
            'city': validated_data.pop('city', ''),
            'hourly_rate': validated_data.pop('hourly_rate', 0.00),
            'years_of_experience': validated_data.pop('years_of_experience', 0)
        }

        with transaction.atomic():
            user = self._create_user(validated_data)
            self._create_profile(user, role, phone)
            
            if role == 'practitioner':
                self._create_practitioner(user, practitioner_data)
            
            return user

# ==============================================================================
# PRACTITIONER APPLICATION SERIALIZERS
# ==============================================================================

class PractitionerApplicationSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = PractitionerApplication
        fields = [
            'id', 'user', 'full_name', 'email', 'status',
            'professional_title', 'qualifications', 'experience_description',
            'specialized_areas', 'id_document', 'certification_documents',
            'profile_photo', 'linkedin_url', 'website_url',
            'submitted_at', 'reviewed_at', 'admin_notes', 'rejection_reason'
        ]
        read_only_fields = ['id', 'submitted_at', 'reviewed_at', 'status']
    
    def get_full_name(self, obj):
        if obj.user:
            return obj.user.get_full_name()
        return "Unknown"

class PractitionerApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PractitionerApplication
        fields = [
            'professional_title', 'qualifications', 'experience_description',
            'specialized_areas', 'id_document', 'certification_documents',
            'profile_photo', 'linkedin_url', 'website_url',
            'terms_accepted', 'data_consent_given'
        ]
    
    def validate(self, data):
        if not data.get('terms_accepted'):
            raise serializers.ValidationError(
                "You must accept the terms and conditions"
            )
        return data

class PractitionerApplicationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PractitionerApplication
        fields = [
            'professional_title', 'qualifications', 'experience_description',
            'specialized_areas', 'id_document', 'certification_documents',
            'profile_photo', 'linkedin_url', 'website_url'
        ]

class PractitionerApplicationReviewSerializer(serializers.ModelSerializer):
    applicant_info = serializers.SerializerMethodField()
    
    class Meta:
        model = PractitionerApplication
        fields = [
            'id', 'status', 'admin_notes', 'rejection_reason',
            'applicant_info', 'qualifications', 'experience_description',
            'specialized_areas', 'id_document', 'certification_documents',
            'profile_photo', 'linkedin_url', 'website_url',
            'submitted_at'
        ]
        read_only_fields = ['id', 'submitted_at']
    
    def get_applicant_info(self, obj):
        if obj.user:
            return {
                'email': obj.user.email,
                'first_name': obj.user.first_name,
                'last_name': obj.user.last_name,
                'full_name': obj.user.get_full_name(),
            }
        return None

# ==============================================================================
# SPECIALTY SERIALIZERS
# ==============================================================================

class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ['id', 'name', 'description']

# ==============================================================================
# PRACTITIONER SERIALIZERS
# ==============================================================================

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

class PractitionerDetailSerializer(PractitionerSerializer):
    application_status = serializers.SerializerMethodField()
    
    class Meta(PractitionerSerializer.Meta):
        fields = PractitionerSerializer.Meta.fields + ['application_status']
    
    def get_application_status(self, obj):
        if hasattr(obj, 'application'):
            return obj.application.status
        return None

class PractitionerUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Practitioner
        fields = [
            'bio', 'city', 'hourly_rate', 'currency',
            'years_of_experience', 'specialties', 'profile_complete'
        ]

# ==============================================================================
# AVAILABILITY SERIALIZERS
# ==============================================================================

class AvailabilitySerializer(serializers.ModelSerializer):
    day_display = serializers.CharField(source='get_day_of_week_display', read_only=True)
    
    class Meta:
        model = Availability
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class AvailabilityCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Availability
        fields = [
            'recurrence_type', 'day_of_week', 'specific_date',
            'start_time', 'end_time', 'is_available', 'notes'
        ]

# ==============================================================================
# CONSULTATION SERIALIZERS
# ==============================================================================

class ConsultationSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source='client.get_full_name', read_only=True)
    practitioner_name = serializers.CharField(
        source='practitioner.user.get_full_name', 
        read_only=True
    )
    
    class Meta:
        model = Consultation
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'version']

class ConsultationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultation
        fields = [
            'practitioner', 'date', 'time', 'duration_minutes', 'client_notes'
        ]

class ConsultationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultation
        fields = ['status', 'practitioner_notes']

# ==============================================================================
# REVIEW SERIALIZERS
# ==============================================================================

class ReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source='reviewer.get_full_name', read_only=True)
    
    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['consultation', 'rating', 'comment']
    
    def validate(self, data):
        consultation = data['consultation']
        if consultation.status != 'completed':
            raise serializers.ValidationError(
                "Can only review completed consultations"
            )
        if hasattr(consultation, 'review'):
            raise serializers.ValidationError(
                "This consultation already has a review"
            )
        return data

# ==============================================================================
# NOTIFICATION SERIALIZERS
# ==============================================================================

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


class NotificationMarkReadSerializer(serializers.Serializer):
    """Serializer for marking notifications as read"""
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    mark_all = serializers.BooleanField(default=False)

# ==============================================================================
# DASHBOARD STATS SERIALIZERS
# ==============================================================================

class ClientDashboardStatsSerializer(serializers.Serializer):
    total_consultations = serializers.IntegerField()
    completed_consultations = serializers.IntegerField()
    upcoming_consultations = serializers.IntegerField()
    cancelled_consultations = serializers.IntegerField()
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending_reviews = serializers.IntegerField()

class PractitionerDashboardStatsSerializer(serializers.Serializer):
    total_consultations = serializers.IntegerField()
    completed_consultations = serializers.IntegerField()
    upcoming_consultations = serializers.IntegerField()
    cancelled_consultations = serializers.IntegerField()
    total_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_rating = serializers.FloatField()