from rest_framework import serializers
from .models import (
    User, UserProfile, Specialty, Practitioner, 
    Availability, Consultation, Review, Notification, PractitionerApplication
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
    """Extended practitioner details"""
    class Meta(PractitionerSerializer.Meta):
        fields = PractitionerSerializer.Meta.fields


class PractitionerUpdateSerializer(serializers.ModelSerializer):
    """Update practitioner profile"""
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
    """Create availability slots"""
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
    """Create a new consultation"""
    class Meta:
        model = Consultation
        fields = [
            'practitioner', 'date', 'time', 'duration_minutes', 'client_notes'
        ]


class ConsultationUpdateSerializer(serializers.ModelSerializer):
    """Update consultation status/notes"""
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
    """Create a new review"""
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
    """Mark notifications as read"""
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    mark_all = serializers.BooleanField(default=False)


# ==============================================================================
# DASHBOARD STATS SERIALIZERS
# ==============================================================================

class ClientDashboardStatsSerializer(serializers.Serializer):
    """Client dashboard statistics"""
    total_consultations = serializers.IntegerField()
    completed_consultations = serializers.IntegerField()
    upcoming_consultations = serializers.IntegerField()
    cancelled_consultations = serializers.IntegerField()
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending_reviews = serializers.IntegerField()


class PractitionerDashboardStatsSerializer(serializers.Serializer):
    """Practitioner dashboard statistics"""
    total_consultations = serializers.IntegerField()
    completed_consultations = serializers.IntegerField()
    upcoming_consultations = serializers.IntegerField()
    cancelled_consultations = serializers.IntegerField()
    total_earnings = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_rating = serializers.FloatField()


# ==============================================================================
# PRACTITIONER APPLICATION SERIALIZERS
# ==============================================================================

class PractitionerApplicationSerializer(serializers.ModelSerializer):
    """Full application details serializer"""
    practitioner_name = serializers.CharField(
        source='practitioner.user.get_full_name', 
        read_only=True
    )
    practitioner_email = serializers.EmailField(
        source='practitioner.user.email', 
        read_only=True
    )
    reviewed_by_name = serializers.CharField(
        source='reviewed_by.get_full_name', 
        read_only=True
    )
    document_urls = serializers.SerializerMethodField()
    
    class Meta:
        model = PractitionerApplication
        fields = '__all__'
        read_only_fields = [
            'practitioner', 'status', 'reviewed_by', 
            'reviewed_at', 'submitted_at', 'created_at', 'updated_at'
        ]
    
    def get_document_urls(self, obj):
        """Get URLs for uploaded documents"""
        urls = {}
        if obj.id_document:
            urls['id_document'] = obj.id_document.url
        if obj.certification_documents:
            urls['certification_documents'] = obj.certification_documents.url
        if obj.profile_photo:
            urls['profile_photo'] = obj.profile_photo.url
        return urls


class PractitionerApplicationCreateSerializer(serializers.ModelSerializer):
    """Create or update application serializer"""
    
    class Meta:
        model = PractitionerApplication
        exclude = ['practitioner', 'status', 'reviewed_by', 'reviewed_at', 'admin_notes', 'rejection_reason']
        extra_kwargs = {
            'id_document': {'required': False},
            'certification_documents': {'required': False},
            'profile_photo': {'required': False},
        }
    
    def validate_terms_accepted(self, value):
        if not value:
            raise serializers.ValidationError("You must accept the terms and conditions")
        return value
    
    def validate_data_consent_given(self, value):
        if not value:
            raise serializers.ValidationError("You must give consent for data processing")
        return value
    
    def validate_qualifications(self, value):
        if not value or len(value.strip()) < 10:
            raise serializers.ValidationError("Please provide detailed qualifications")
        return value
    
    def validate_experience_description(self, value):
        if not value or len(value.strip()) < 20:
            raise serializers.ValidationError("Please provide a detailed experience description")
        return value


class PractitionerApplicationListSerializer(serializers.ModelSerializer):
    """Lightweight list serializer for applications"""
    practitioner_name = serializers.CharField(
        source='practitioner.user.get_full_name', 
        read_only=True
    )
    practitioner_email = serializers.EmailField(
        source='practitioner.user.email', 
        read_only=True
    )
    
    class Meta:
        model = PractitionerApplication
        fields = [
            'id', 
            'practitioner_name', 
            'practitioner_email',
            'professional_title', 
            'status', 
            'created_at', 
            'submitted_at'
        ]


class PractitionerApplicationStatusSerializer(serializers.Serializer):
    """Simple status check serializer"""
    has_application = serializers.BooleanField()
    status = serializers.CharField(required=False)
    professional_title = serializers.CharField(required=False)
    submitted_at = serializers.DateTimeField(required=False)
    can_edit = serializers.BooleanField(required=False)


# ==============================================================================
# ADMIN APPLICATION ACTION SERIALIZERS
# ==============================================================================

class AdminApplicationActionSerializer(serializers.Serializer):
    """Admin approve/reject actions"""
    
    ACTION_CHOICES = [
        ('approve', '✅ Approve'),
        ('reject', '❌ Reject'),
    ]
    
    action = serializers.ChoiceField(choices=ACTION_CHOICES)
    reason = serializers.CharField(
        required=False, 
        allow_blank=True,
        help_text="Rejection reason (required for reject)"
    )
    admin_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Internal admin notes"
    )
    
    def validate(self, data):
        if data['action'] == 'reject' and not data.get('reason'):
            raise serializers.ValidationError({
                'reason': 'Rejection reason is required when rejecting an application'
            })
        return data


class AdminApplicationReviewSerializer(serializers.ModelSerializer):
    """Admin review notes serializer"""
    
    class Meta:
        model = PractitionerApplication
        fields = ['admin_notes', 'rejection_reason']


class AdminApplicationFilterSerializer(serializers.Serializer):
    """Filter applications by status"""
    status = serializers.ChoiceField(
        choices=[
            ('draft', 'Draft'),
            ('pending', 'Pending Review'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('info_needed', 'Info Needed'),
        ],
        required=False
    )
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    search = serializers.CharField(required=False)


# ==============================================================================
# APPLICATION STATS SERIALIZERS
# ==============================================================================

class ApplicationStatsSerializer(serializers.Serializer):
    """Application statistics for admin dashboard"""
    total = serializers.IntegerField()
    draft = serializers.IntegerField()
    pending = serializers.IntegerField()
    approved = serializers.IntegerField()
    rejected = serializers.IntegerField()
    info_needed = serializers.IntegerField()
    by_status = serializers.DictField(child=serializers.IntegerField())