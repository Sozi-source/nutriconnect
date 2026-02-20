from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from datetime import time

# Abstract base class for timestamped models
class TimeStampedModel(models.Model):
    """
    Abstract model that provides self-updating 'created_at' and 'updated_at' fields.
    """
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
    
    def get_short_name(self):
        return self.first_name

# User Profile Model
class UserProfile(models.Model):
    USER_ROLES = [
        ('client', 'Client'),
        ('practitioner', 'Practitioner'),
    ]
    
    # Phone number validator
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

# Practitioner Model
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
        help_text="Hourly rate in selected currency"
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='practitioner')
    specialties = models.ManyToManyField(Specialty, related_name='practitioner')
    bio = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, db_index=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    is_verified = models.BooleanField(default=False, db_index=True)
    profile_complete = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['city', 'is_verified']),
            models.Index(fields=['years_of_experience', 'hourly_rate']),
            models.Index(fields=['is_verified', 'city']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.city}"
    
    def is_available_at(self, date, time):
        """
        Check if practitioner is available at a specific date and time.
        
        Args:
            date: date object
            time: time object
            
        Returns:
            bool: True if available, False otherwise
        """
        day_of_week = date.weekday()
        
        # First check if practitioner is unavailable on this date
        if self.availabilities.filter(
            recurrence_type=Availability.RecurrenceType.UNAVAILABLE,
            specific_date=date,
            is_available=False
        ).exists():
            return False
        
        # Check weekly recurring availability
        weekly_available = self.availabilities.filter(
            recurrence_type=Availability.RecurrenceType.WEEKLY,
            day_of_week=day_of_week,
            start_time__lte=time,
            end_time__gte=time,
            is_available=True
        ).exists()
        
        if weekly_available:
            return True
        
        # Check one-time availability
        one_time_available = self.availabilities.filter(
            recurrence_type=Availability.RecurrenceType.ONE_TIME,
            specific_date=date,
            start_time__lte=time,
            end_time__gte=time,
            is_available=True
        ).exists()
        
        return one_time_available
    
    def get_upcoming_consultations(self, days=30):
        """Get consultations for the next X days"""
        from django.utils import timezone
        from datetime import timedelta
        
        end_date = timezone.now().date() + timedelta(days=days)
        return self.consultations.filter(
            date__gte=timezone.now().date(),
            date__lte=end_date,
            status__in=[Consultation.Status.BOOKED, Consultation.Status.COMPLETED]
        ).order_by('date', 'time')

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

    practitioner = models.ForeignKey(
        Practitioner, 
        on_delete=models.CASCADE, 
        related_name='availabilities'
    )
    
    # Type of availability
    recurrence_type = models.CharField(
        max_length=20,
        choices=RecurrenceType.choices,
        default=RecurrenceType.WEEKLY
    )
    
    # Weekly recurring fields
    day_of_week = models.IntegerField(
        choices=Day.choices,
        null=True,
        blank=True,
        help_text="For weekly recurring availability (0=Monday, 6=Sunday)"
    )
    
    # One-time or date-specific fields
    specific_date = models.DateField(
        null=True, 
        blank=True,
        help_text="For one-time availability or unavailable blocks"
    )
    
    # Time range
    start_time = models.TimeField(help_text="Format: HH:MM:SS")
    end_time = models.TimeField(help_text="Format: HH:MM:SS")
    
    # Optional fields
    is_available = models.BooleanField(
        default=True,
        help_text="False for unavailable blocks (vacation, time off, holidays)"
    )
    notes = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Reason for unavailability (e.g., 'Vacation', 'Conference', 'Public Holiday')"
    )

    class Meta:
        ordering = ['practitioner', 'day_of_week', 'start_time']
        indexes = [
            models.Index(fields=['practitioner', 'recurrence_type']),
            models.Index(fields=['practitioner', 'specific_date']),
            models.Index(fields=['practitioner', 'day_of_week']),
            models.Index(fields=['practitioner', 'is_available']),
            models.Index(fields=['specific_date', 'is_available']),
        ]
        constraints = [
            # Valid weekly availability
            models.CheckConstraint(
                condition=models.Q(
                    recurrence_type='weekly',
                    day_of_week__isnull=False,
                    specific_date__isnull=True
                ),
                name='valid_weekly_availability'
            ),
            # Valid one-time availability
            models.CheckConstraint(
                condition=models.Q(
                    recurrence_type='one_time',
                    day_of_week__isnull=True,
                    specific_date__isnull=False
                ),
                name='valid_one_time_availability'
            ),
            # Valid unavailable blocks
            models.CheckConstraint(
                condition=models.Q(
                    recurrence_type='unavailable',
                    specific_date__isnull=False
                ),
                name='valid_unavailable_block'
            ),
            # End time after start time
            models.CheckConstraint(
                condition=models.Q(end_time__gt=models.F('start_time')),
                name='end_time_after_start_time'
            ),
        ]

    def __str__(self):
        if self.recurrence_type == 'weekly':
            day_name = self.get_day_of_week_display()
            status = "✅ Available" if self.is_available else "❌ Unavailable"
            return f"{self.practitioner} - {day_name} {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')} ({status})"
        else:
            date_str = self.specific_date.strftime('%Y-%m-%d')
            status = "✅ Available" if self.is_available else "❌ Unavailable"
            return f"{self.practitioner} - {date_str} {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')} ({status})"

    def clean(self):
        """Validate the availability entry"""
        # Validate based on recurrence type
        if self.recurrence_type == 'weekly' and self.day_of_week is None:
            raise ValidationError({'day_of_week': 'Weekly availability requires day_of_week'})
        if self.recurrence_type in ['one_time', 'unavailable'] and self.specific_date is None:
            raise ValidationError({'specific_date': f'{self.get_recurrence_type_display()} requires specific_date'})
        
        # Validate time range
        if self.start_time >= self.end_time:
            raise ValidationError('End time must be after start time')
        
        # Validate time slots are in 30-minute increments (optional business rule)
        if self.start_time.minute % 30 != 0 or self.end_time.minute % 30 != 0:
            raise ValidationError('Time slots must be in 30-minute increments')
        
        # Prevent duplicate availability
        if self.recurrence_type == 'weekly' and self.day_of_week is not None:
            if Availability.objects.filter(
                practitioner=self.practitioner,
                recurrence_type='weekly',
                day_of_week=self.day_of_week,
                start_time=self.start_time
            ).exclude(pk=self.pk).exists():
                raise ValidationError('This weekly time slot already exists')
        
        if self.recurrence_type == 'one_time' and self.specific_date:
            if Availability.objects.filter(
                practitioner=self.practitioner,
                recurrence_type='one_time',
                specific_date=self.specific_date,
                start_time=self.start_time
            ).exclude(pk=self.pk).exists():
                raise ValidationError('This one-time slot already exists')
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

# Consultation Model
class Consultation(TimeStampedModel):
    class Status(models.TextChoices):
        BOOKED = 'booked', 'Booked'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        NO_SHOW = 'no_show', 'No Show'

    client = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='consultations', 
        limit_choices_to={'profile__role': 'client'}
    )
    practitioner = models.ForeignKey(
        Practitioner, 
        on_delete=models.CASCADE, 
        related_name='consultations'
    )
    date = models.DateField(db_index=True)
    time = models.TimeField()
    status = models.CharField(
        max_length=50, 
        choices=Status.choices, 
        default=Status.BOOKED
    )
    duration_minutes = models.PositiveIntegerField(default=60)
    client_notes = models.TextField(blank=True, null=True)
    practitioner_notes = models.TextField(blank=True, null=True)
    version = models.IntegerField(
        default=1,
        help_text="Optimistic locking version field to prevent double booking"
    )

    class Meta:
        unique_together = ['practitioner', 'date', 'time']
        ordering = ['-date', '-time']
        indexes = [
            models.Index(fields=['client', 'status']),
            models.Index(fields=['practitioner', 'status']),
            models.Index(fields=['date', 'status']),
            models.Index(fields=['client', 'date']),
        ]

    def __str__(self):
        return f"{self.client.get_full_name()} with {self.practitioner} on {self.date} at {self.time.strftime('%H:%M')}"
    
    def can_cancel(self):
        """Check if consultation can be cancelled (24h before appointment)"""
        from django.utils import timezone
        from datetime import datetime, timedelta
        
        appointment_datetime = datetime.combine(self.date, self.time)
        time_diff = appointment_datetime - timezone.now()
        return time_diff > timedelta(hours=24)

# Review Model
class Review(TimeStampedModel):
    consultation = models.OneToOneField(
        Consultation, 
        on_delete=models.CASCADE, 
        related_name='review'
    )
    reviewer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='reviews', 
        null=True, 
        blank=True
    )
    rating = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 6)],
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['consultation', 'rating']),
            models.Index(fields=['reviewer', 'created_at']),
        ]

    def __str__(self):
        return f"Review by {self.reviewer.email if self.reviewer else 'Anonymous'} for {self.consultation} - {self.rating}⭐"
    
    def clean(self):
        """Ensure review is for a completed consultation"""
        if self.consultation.status != Consultation.Status.COMPLETED:
            raise ValidationError('Reviews can only be created for completed consultations')