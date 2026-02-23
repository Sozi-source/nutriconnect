from rest_framework import serializers
from .models import (
    User, UserProfile, Specialty, Practitioner, 
    Availability, Consultation, Review, Notification,
    PractitionerApplication
)
from django.db import transaction

# ==============================================================================
# PROFILE SERIALIZERS
#==============================================================================

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile data"""
    class Meta:
        model = UserProfile
        fields = ['id', 'role', 'phone']


# ==============================================================================
# USER SERIALIZERS
# ==============================================================================

class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data with profile nested"""
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'profile']


# ==============================================================================
# AUTHENTICATION SERIALIZERS
# ==============================================================================

class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration (both client and practitioner)"""
    # Core fields
    password = serializers.CharField(write_only=True, min_length=8)
    role = serializers.ChoiceField(choices=['client', 'practitioner'], write_only=True)
    phone = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    # Practitioner-specific fields (optional)
    bio = serializers.CharField(write_only=True, required=False, allow_blank=True)
    city = serializers.CharField(write_only=True, required=False, allow_blank=True)
    hourly_rate = serializers.DecimalField(
        max_digits=10, decimal_places=2, 
        write_only=True, required=False
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
        """Helper method to create user"""
        return User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
    
    def _create_profile(self, user, role, phone):
        """Helper method to create user profile"""
        return UserProfile.objects.create(
            user=user,
            role=role,
            phone=phone
        )
    
    def _create_practitioner(self, user, practitioner_data):
        """Helper method to create practitioner record"""
        return Practitioner.objects.create(
            user=user,
            bio=practitioner_data.get('bio', ''),
            city=practitioner_data.get('city', ''),
            hourly_rate=practitioner_data.get('hourly_rate', 0.00),
            years_of_experience=practitioner_data.get('years_of_experience', 0),
            currency='KES',
            is_verified=False,
            profile_complete=False
        )
    
    def create(self, validated_data):
        """Main create method orchestrating the registration process"""
        # Extract data
        role = validated_data.pop('role')
        phone = validated_data.pop('phone', '')
        
        # Extract practitioner data
        practitioner_data = {
            'bio': validated_data.pop('bio', ''),
            'city': validated_data.pop('city', ''),
            'hourly_rate': validated_data.pop('hourly_rate', 0.00),
            'years_of_experience': validated_data.pop('years_of_experience', 0)
        }

        with transaction.atomic():
            # Create user
            user = self._create_user(validated_data)
            
            # Create profile
            self._create_profile(user, role, phone)
            
            # Create practitioner if role is practitioner
            if role == 'practitioner':
                self._create_practitioner(user, practitioner_data)
                # NOTE: PractitionerApplication is NOT created here
                # This keeps registration simple and separate from the application process
            
            return user


# ==============================================================================
# PRACTITIONER APPLICATION SERIALIZERS
# ==============================================================================

class PractitionerApplicationSerializer(serializers.ModelSerializer):
    """Serializer for practitioner applications"""
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
    """Serializer for creating a new practitioner application"""
    class Meta:
        model = PractitionerApplication
        fields = [
            'professional_title', 'qualifications', 'experience_description',
            'specialized_areas', 'id_document', 'certification_documents',
            'profile_photo', 'linkedin_url', 'website_url',
            'terms_accepted', 'data_consent_given'
        ]
    
    def validate(self, data):
        """Validate that terms are accepted"""
        if not data.get('terms_accepted'):
            raise serializers.ValidationError(
                "You must accept the terms and conditions"
            )
        return data
    
    def create(self, validated_data):
        """Create application for existing practitioner"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            # Check if user has practitioner profile
            if not hasattr(user, 'practitioner'):
                raise serializers.ValidationError(
                    "User does not have a practitioner profile"
                )
            # Check if application already exists
            if PractitionerApplication.objects.filter(user=user).exists():
                raise serializers.ValidationError(
                    "Application already exists for this user"
                )
            
            validated_data['user'] = user
            validated_data['practitioner'] = user.practitioner
            return super().create(validated_data)
        raise serializers.ValidationError("Authentication required")


class PractitionerApplicationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating an existing application"""
    class Meta:
        model = PractitionerApplication
        fields = [
            'professional_title', 'qualifications', 'experience_description',
            'specialized_areas', 'id_document', 'certification_documents',
            'profile_photo', 'linkedin_url', 'website_url'
        ]


class PractitionerApplicationReviewSerializer(serializers.ModelSerializer):
    """Serializer for admin review of applications"""
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
        """Get detailed applicant information"""
        if obj.user:
            return {
                'email': obj.user.email,
                'first_name': obj.user.first_name,
                'last_name': obj.user.last_name,
                'full_name': obj.user.get_full_name(),
                'profile': UserProfileSerializer(obj.user.profile).data if hasattr(obj.user, 'profile') else None
            }
        return None


# ==============================================================================
# SPECIALTY SERIALIZERS
# ==============================================================================

class SpecialtySerializer(serializers.ModelSerializer):
    """Serializer for practitioner specialties"""
    class Meta:
        model = Specialty
        fields = ['id', 'name', 'description']


# ==============================================================================
# PRACTITIONER SERIALIZERS
# ==============================================================================

class PractitionerSerializer(serializers.ModelSerializer):
    """Serializer for practitioner profiles"""
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
        """Get practitioner's full name from user"""
        return obj.user.get_full_name()


class PractitionerDetailSerializer(PractitionerSerializer):
    """Detailed practitioner serializer with additional fields"""
    application_status = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    
    class Meta(PractitionerSerializer.Meta):
        fields = PractitionerSerializer.Meta.fields + [
            'application_status', 'total_reviews', 'average_rating'
        ]
    
    def get_application_status(self, obj):
        """Get practitioner's application status"""
        if hasattr(obj, 'application'):
            return obj.application.status
        return None
    
    def get_total_reviews(self, obj):
        """Get total number of reviews"""
        # This would need a Review model relation
        return 0
    
    def get_average_rating(self, obj):
        """Get average rating"""
        # This would need a Review model relation
        return 0


class PractitionerCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a practitioner (internal use)"""
    class Meta:
        model = Practitioner
        fields = [
            'bio', 'city', 'hourly_rate', 'currency',
            'years_of_experience', 'specialties'
        ]


class PractitionerUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating practitioner profile"""
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
    """Serializer for practitioner availability"""
    day_display = serializers.CharField(source='get_day_of_week_display', read_only=True)
    
    class Meta:
        model = Availability
        fields = [
            'id', 'practitioner', 'recurrence_type', 'day_of_week',
            'day_display', 'specific_date', 'start_time', 'end_time',
            'is_available', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class AvailabilityCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating availability slots"""
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
    """Serializer for consultations"""
    client_name = serializers.CharField(source='client.get_full_name', read_only=True)
    practitioner_name = serializers.CharField(
        source='practitioner.user.get_full_name', 
        read_only=True
    )
    
    class Meta:
        model = Consultation
        fields = [
            'id', 'client', 'client_name', 'practitioner', 'practitioner_name',
            'date', 'time', 'status', 'duration_minutes',
            'client_notes', 'practitioner_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'version']


class ConsultationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating consultations"""
    class Meta:
        model = Consultation
        fields = [
            'practitioner', 'date', 'time', 'duration_minutes', 'client_notes'
        ]


class ConsultationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating consultations"""
    class Meta:
        model = Consultation
        fields = ['status', 'practitioner_notes']


# ==============================================================================
# REVIEW SERIALIZERS
# ==============================================================================

class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for reviews"""
    reviewer_name = serializers.CharField(source='reviewer.get_full_name', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'consultation', 'reviewer', 'reviewer_name',
            'rating', 'comment', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating reviews"""
    class Meta:
        model = Review
        fields = ['consultation', 'rating', 'comment']
    
    def validate(self, data):
        """Ensure consultation is completed and not already reviewed"""
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
    """Serializer for notifications"""
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'message', 
            'data', 'is_read', 'created_at', 'read_at', 'time_ago'
        ]
        read_only_fields = ['id', 'created_at', 'read_at']
    
    def get_time_ago(self, obj):
        """Get human-readable time since creation"""
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
    """Serializer for client dashboard statistics"""
    total_consultations = serializers.IntegerField()
    completed_consultations = serializers.IntegerField()
    upcoming_consultations = serializers.IntegerField()
    cancelled_consultations = serializers.IntegerField()
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending_reviews = serializers.IntegerField()


class PractitionerDashboardStatsSerializer(serializers.Serializer):
    """Serializer for practitioner dashboard statistics"""
    total_consultations = serializers.IntegerField()
    completed_consultations = serializers.IntegerField()
    upcoming_consultations = serializers.IntegerField()
    cancelled_consultations = serializers.IntegerField()
    total_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_rating = serializers.FloatField()