from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from datetime import time

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