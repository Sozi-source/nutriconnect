from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from datetime import time
from django.utils import timezone  # Add this import for timezone.now()

# Abstract base class for timestamped models
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

# Custom User Manager
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('email must be provided')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)

# User Model
class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.email}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

# User Profile Model
class UserProfile(models.Model):
    USER_ROLES = [
        ('client', 'Client'),
        ('practitioner', 'Practitioner'),
    ]
    
    phone_validator = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in format: '+254712345678' (up to 15 digits)"
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=50, choices=USER_ROLES, default='client')
    phone = models.CharField(
        max_length=20, 
        null=True, 
        blank=True,
        validators=[phone_validator],
        help_text="Format: +254712345678"
    )

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.role}"

# Specialty Model
class Specialty(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

# Practitioner Model (SIMPLIFIED)
class Practitioner(TimeStampedModel):
    CURRENCY_CHOICES = [
        ('KES', 'Kenyan Shilling'),
        ('USD', 'US Dollar'),
    ]
    
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='KES')
    hourly_rate = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        default=0.00,
        null=True,
        blank=True
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='practitioner')
    specialties = models.ManyToManyField(Specialty, related_name='practitioner', blank=True)
    bio = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, db_index=True, blank=True, default='')
    years_of_experience = models.PositiveIntegerField(default=0, blank=True)
    is_verified = models.BooleanField(default=False, db_index=True)  # Admin approval
    profile_complete = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['city', 'is_verified']),
            models.Index(fields=['years_of_experience', 'hourly_rate']),
            models.Index(fields=['is_verified', 'city']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.city}"

# ==============================================================================
# PRACTITIONER APPLICATION MODEL - ADD THIS SECTION
# ==============================================================================

class PractitionerApplication(TimeStampedModel):
    """
    Model to track practitioner applications for verification
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('info_needed', 'More Info Needed'),
    ]
    
    practitioner = models.OneToOneField(Practitioner, on_delete=models.CASCADE, related_name='application')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_applications')
    
    # Application details
    qualifications = models.TextField(help_text="List your qualifications and certifications")
    experience_description = models.TextField(help_text="Describe your relevant experience")
    id_document = models.FileField(upload_to='applications/id/', null=True, blank=True)
    certification_documents = models.FileField(upload_to='applications/certifications/', null=True, blank=True)
    
    # Admin notes
    admin_notes = models.TextField(blank=True, null=True, help_text="Internal notes for admin")
    rejection_reason = models.TextField(blank=True, null=True, help_text="Reason if rejected")
    
    class Meta:
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['status', 'submitted_at']),
        ]
    
    def __str__(self):
        return f"Application for {self.practitioner.user.get_full_name()} - {self.status}"
    
    def approve(self, admin_user):
        """Approve the application and verify the practitioner"""
        self.status = 'approved'
        self.reviewed_at = timezone.now()
        self.reviewed_by = admin_user
        self.save()
        
        # Verify the practitioner
        self.practitioner.is_verified = True
        self.practitioner.save()
    
    def reject(self, admin_user, reason):
        """Reject the application"""
        self.status = 'rejected'
        self.reviewed_at = timezone.now()
        self.reviewed_by = admin_user
        self.rejection_reason = reason
        self.save()
    
    def request_more_info(self, admin_user, notes):
        """Request more information from the practitioner"""
        self.status = 'info_needed'
        self.reviewed_at = timezone.now()
        self.reviewed_by = admin_user
        self.admin_notes = notes
        self.save()

# ==============================================================================
# END OF PRACTITIONER APPLICATION MODEL
# ==============================================================================

# Availability Model
class Availability(TimeStampedModel):
    class Day(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"
    
    class RecurrenceType(models.TextChoices):
        WEEKLY = 'weekly', 'Weekly Recurring'
        ONE_TIME = 'one_time', 'One-Time Adjustment'
        UNAVAILABLE = 'unavailable', 'Unavailable Block'

    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE, related_name='availabilities')
    recurrence_type = models.CharField(max_length=20, choices=RecurrenceType.choices, default=RecurrenceType.WEEKLY)
    day_of_week = models.IntegerField(choices=Day.choices, null=True, blank=True)
    specific_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    notes = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ['practitioner', 'day_of_week', 'start_time']
    
    def __str__(self):
        return f"{self.practitioner} - {self.start_time}"

# Consultation Model
class Consultation(TimeStampedModel):
    class Status(models.TextChoices):
        BOOKED = 'booked', 'Booked'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        NO_SHOW = 'no_show', 'No Show'

    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='consultations')
    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE, related_name='consultations')
    date = models.DateField(db_index=True)
    time = models.TimeField()
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.BOOKED)
    duration_minutes = models.PositiveIntegerField(default=60)
    client_notes = models.TextField(blank=True, null=True)
    practitioner_notes = models.TextField(blank=True, null=True)
    version = models.IntegerField(default=1)

    class Meta:
        unique_together = ['practitioner', 'date', 'time']
        ordering = ['-date', '-time']
    
    def __str__(self):
        return f"{self.client.get_full_name()} with {self.practitioner}"

# Review Model
class Review(TimeStampedModel):
    consultation = models.OneToOneField(Consultation, on_delete=models.CASCADE, related_name='review')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Review by {self.reviewer.email} - {self.rating}⭐"
#=====================================================================================================
# NOTIFICATION MODEL
#=====================================================================================================
class Notification(TimeStampedModel):
    """
    Notification model for user alerts and updates
    """
    class NotificationType(models.TextChoices):
        CONSULTATION_REQUEST = 'consultation_request', 'New Consultation Request'
        CONSULTATION_CONFIRMED = 'consultation_confirmed', 'Consultation Confirmed'
        CONSULTATION_CANCELLED = 'consultation_cancelled', 'Consultation Cancelled'
        CONSULTATION_COMPLETED = 'consultation_completed', 'Consultation Completed'
        REVIEW_RECEIVED = 'review_received', 'New Review Received'
        PAYMENT_RECEIVED = 'payment_received', 'Payment Received'
        PRACTITIONER_VERIFIED = 'practitioner_verified', 'Account Verified'
        SYSTEM = 'system', 'System Notification'

    recipient = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        db_index=True
    )
    notification_type = models.CharField(
        max_length=30, 
        choices=NotificationType.choices,
        db_index=True
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)  # Store additional data like consultation_id, review_id
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.recipient.email} - {self.title[:30]}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at', 'updated_at'])
    
    @classmethod
    def mark_all_as_read(cls, user):
        """Mark all unread notifications as read for a user"""
        return cls.objects.filter(recipient=user, is_read=False).update(
            is_read=True,
            read_at=timezone.now(),
            updated_at=timezone.now()
        )