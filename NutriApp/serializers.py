from rest_framework import serializers
from .models import User, UserProfile, Specialty, Consultation, Availability, Review, Practitioner
from django.core.exceptions import ValidationError
from datetime import datetime

# ==================== USER & PROFILE SERIALIZERS ====================

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'role', 'phone']

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    profile = UserProfileSerializer(read_only=True)

    role = serializers.ChoiceField(
        choices=['client', 'practitioner'],
        write_only=True,
        required=False,
        default='client'
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
        phone = validated_data.pop('phone', '')

        # Create user
        user = User.objects.create_user(**validated_data)

        # Create profile
        profile = UserProfile.objects.create(
            user=user, 
            role=role, 
            phone=phone
        )
        
        # Auto-create practitioner if role is practitioner
        if role == 'practitioner':
            Practitioner.objects.create(
                user=user,
                hourly_rate=0.00,
                currency='KES',
                city='',
                bio='',
                years_of_experience=0,
                is_verified=False,
                profile_complete=False
            )
        
        return user

# ==================== SPECIALTY SERIALIZER ====================

class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ['id', 'name', 'description']

# ==================== PRACTITIONER SERIALIZER ====================

class PractitionerSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    specialties = SpecialtySerializer(many=True, read_only=True)
    full_name = serializers.SerializerMethodField()
    availability_count = serializers.SerializerMethodField()

    class Meta:
        model = Practitioner
        fields = [
            'id', 'user', 'first_name', 'last_name', 'full_name', 'email', 
            'bio', 'currency', 'hourly_rate', 'city', 'years_of_experience',
            'is_verified', 'profile_complete', 'specialties', 'availability_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'is_verified']

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    
    def get_availability_count(self, obj):
        return obj.availabilities.filter(is_available=True).count()

class PractitionerDetailSerializer(PractitionerSerializer):
    """Detailed serializer with availability included"""
    availabilities = serializers.SerializerMethodField()
    
    class Meta(PractitionerSerializer.Meta):
        fields = PractitionerSerializer.Meta.fields + ['availabilities']
    
    def get_availabilities(self, obj):
        from .serializers import AvailabilitySerializer
        availabilities = obj.availabilities.filter(is_available=True)
        return AvailabilitySerializer(availabilities, many=True).data

# ==================== AVAILABILITY SERIALIZERS ====================

class AvailabilitySerializer(serializers.ModelSerializer):
    practitioner_name = serializers.CharField(source='practitioner.user.get_full_name', read_only=True)
    day_display = serializers.CharField(source='get_day_of_week_display', read_only=True)
    recurrence_display = serializers.CharField(source='get_recurrence_type_display', read_only=True)
    
    class Meta:
        model = Availability
        fields = [
            'id', 'practitioner', 'practitioner_name', 
            'recurrence_type', 'recurrence_display',
            'day_of_week', 'day_display', 'specific_date', 
            'start_time', 'end_time', 'is_available', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        """Additional validation for availability slots"""
        practitioner = data.get('practitioner')
        
        if practitioner and not practitioner.is_verified:
            raise serializers.ValidationError(
                "Your practitioner profile must be verified before setting availability"
            )
        
        if data.get('start_time') and data.get('end_time'):
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError("End time must be after start time")
        
        return data

class BulkAvailabilitySerializer(serializers.Serializer):
    """For creating multiple weekly slots at once"""
    practitioner_id = serializers.IntegerField()
    days = serializers.ListField(
        child=serializers.ChoiceField(choices=Availability.Day.choices)
    )
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    is_available = serializers.BooleanField(default=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError("End time must be after start time")
        return data
    
    def create(self, validated_data):
        from .models import Practitioner
        practitioner = Practitioner.objects.get(id=validated_data['practitioner_id'])
        created_slots = []
        
        for day in validated_data['days']:
            availability, created = Availability.objects.get_or_create(
                practitioner=practitioner,
                recurrence_type='weekly',
                day_of_week=day,
                start_time=validated_data['start_time'],
                defaults={
                    'end_time': validated_data['end_time'],
                    'is_available': validated_data.get('is_available', True),
                    'notes': validated_data.get('notes', '')
                }
            )
            if created:
                created_slots.append(availability)
        
        return created_slots

class TimeSlotSerializer(serializers.Serializer):
    """Represents an available time slot for frontend calendar"""
    date = serializers.DateField()
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    practitioner_id = serializers.IntegerField()
    practitioner_name = serializers.CharField()
    formatted_time = serializers.SerializerMethodField()
    
    def get_formatted_time(self, obj):
        return f"{obj['start_time'].strftime('%H:%M')} - {obj['end_time'].strftime('%H:%M')}"

# ==================== CONSULTATION SERIALIZERS ====================

class ConsultationSerializer(serializers.ModelSerializer):
    practitioner_name = serializers.CharField(source='practitioner.user.get_full_name', read_only=True)
    client_name = serializers.CharField(source='client.get_full_name', read_only=True)
    practitioner_details = PractitionerSerializer(source='practitioner', read_only=True)
    formatted_date = serializers.SerializerMethodField()
    formatted_time = serializers.SerializerMethodField()
    
    class Meta:
        model = Consultation
        fields = [
            'id', 'client', 'client_name', 'practitioner', 'practitioner_name',
            'practitioner_details', 'date', 'formatted_date', 'time', 'formatted_time',
            'status', 'duration_minutes', 'client_notes', 'practitioner_notes',
            'created_at', 'updated_at', 'version'
        ]
        read_only_fields = ['client', 'status', 'version', 'created_at', 'updated_at']
        extra_kwargs = {
            'practitioner': {'write_only': True}
        }
    
    def get_formatted_date(self, obj):
        return obj.date.strftime('%B %d, %Y')
    
    def get_formatted_time(self, obj):
        return obj.time.strftime('%I:%M %p')
    
    def validate(self, data):
        # This is for READ operations only
        return data


class ConsultationCreateSerializer(serializers.ModelSerializer):
    """Separate serializer for creation to handle validation properly"""
    class Meta:
        model = Consultation
        fields = ['practitioner', 'date', 'time', 'duration_minutes', 'client_notes']
    
    def validate(self, data):
        # Get the current user from context
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required")
        
        practitioner_id = data.get('practitioner')
        booking_date = data.get('date')
        booking_time = data.get('time')
        
        if not all([practitioner_id, booking_date, booking_time]):
            return data
        
        # Get the practitioner object for validation ONLY
        from .models import Practitioner, Availability, Consultation
        from django.utils import timezone
        from datetime import datetime
        
        try:
            practitioner = Practitioner.objects.get(id=practitioner_id)
        except Practitioner.DoesNotExist:
            raise serializers.ValidationError({
                'practitioner': 'Practitioner with this ID does not exist'
            })
        
        # Check if already booked
        if Consultation.objects.filter(
            practitioner=practitioner,
            date=booking_date,
            time=booking_time,
            status__in=['booked', 'completed']
        ).exists():
            raise serializers.ValidationError("This time slot is already booked")
        
        # Check unavailable blocks
        if Availability.objects.filter(
            practitioner=practitioner,
            recurrence_type='unavailable',
            specific_date=booking_date,
            is_available=False
        ).exists():
            raise serializers.ValidationError("Practitioner is unavailable on this date")
        
        # Check availability using the practitioner's method
        if not practitioner.is_available_at(booking_date, booking_time):
            raise serializers.ValidationError(
                "Practitioner is not available at this time. Please check their availability calendar."
            )
        
        # Check if booking is in the past
        booking_datetime = datetime.combine(booking_date, booking_time)
        if timezone.is_naive(booking_datetime):
            booking_datetime = timezone.make_aware(booking_datetime)
        
        if booking_datetime < timezone.now():
            raise serializers.ValidationError("Cannot book appointments in the past")
        
        # Add client to data - but DO NOT modify practitioner
        data['client'] = request.user
        
        # IMPORTANT: practitioner remains as ID in data, NOT replaced with object
        return data

# ==================== REVIEW SERIALIZER ====================

class ReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.SerializerMethodField()
    consultation_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'consultation', 'consultation_details', 
            'reviewer', 'reviewer_name', 'rating', 'comment', 'created_at'
        ]
        read_only_fields = ['created_at', 'reviewer']
    
    def get_reviewer_name(self, obj):
        if obj.reviewer:
            return obj.reviewer.get_full_name()
        return "Anonymous"
    
    def get_consultation_details(self, obj):
        return {
            'date': obj.consultation.date.strftime('%Y-%m-%d'),
            'time': obj.consultation.time.strftime('%H:%M'),
            'practitioner': obj.consultation.practitioner.user.get_full_name()
        }
    
    def validate(self, data):
        consultation = data.get('consultation')
        
        # Ensure consultation is completed
        if consultation and consultation.status != 'completed':
            raise serializers.ValidationError(
                "Reviews can only be created for completed consultations"
            )
        
        # Ensure user hasn't already reviewed this consultation
        request = self.context.get('request')
        if request and consultation and Review.objects.filter(
            consultation=consultation,
            reviewer=request.user
        ).exists():
            raise serializers.ValidationError("You have already reviewed this consultation")
        
        return data
    
    def create(self, validated_data):
        validated_data['reviewer'] = self.context['request'].user
        return super().create(validated_data)

# ==================== METRICS SERIALIZERS ====================

class MetricsResponseSerializer(serializers.Serializer):
    """Serializer for dashboard metrics"""
    as_client = serializers.DictField()
    as_practitioner = serializers.DictField()
    
    class Meta:
        fields = ['as_client', 'as_practitioner']