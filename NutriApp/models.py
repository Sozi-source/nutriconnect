from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('email must be provided')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user
    # create superuser
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not extra_fields.get("is_staff"):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get("is_superuser"):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    first_name= models.CharField(max_length=150)
    last_name= models.CharField(max_length=150)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name}-{self.email}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        return self.first_name

class UserProfile(models.Model):
    
    USER_ROLES=[
        ('client', 'Client'),
        ('practitioner', 'Practitioner'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=50, choices=USER_ROLES, default='client')
    phone = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()}- {self.role}"


class Specialty(models.Model):
    name= models.CharField(max_length=200, unique=True)
    description= models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Practitioner(models.Model):
    CURRENCY_CHOICES = [
        ('KES', 'Kenyan Shilling'),
        ('USD', 'US Dollar'),
    ]
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='KES')
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='practitioner')
    specialties = models.ManyToManyField(Specialty, related_name='practitioner')
    bio = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, db_index=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    is_verified = models.BooleanField(default=False, db_index=True)
    profile_complete= models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes =[
            models.Index(fields=['city', 'is_verified']),
            models.Index(fields=['years_of_experience', 'hourly_rate'])
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()}-{self.city}"

class Availability(models.Model):
    class Day(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE, related_name='availabilities')
    day_of_week = models.IntegerField(choices=Day.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        unique_together =['practitioner', 'day_of_week', 'start_time'] #prevent duplicate slots
        ordering = ['day_of_week', 'start_time']


    def __str__(self):
        return f"{self.practitioner}-{self.get_day_of_week_display()} {self.start_time}-{self.end_time}"

class Consultation(models.Model):
    class Status(models.TextChoices):
        BOOKED = 'booked', 'Booked'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'
        NO_SHOW = 'no_show', 'No Show'

    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='consultations', limit_choices_to={'profile__role':'client'})
    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE, related_name='consultations')
    date = models.DateField(db_index=True)
    time = models.TimeField()
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.BOOKED)
    duration_minutes = models.PositiveIntegerField(default=60)
    client_notes = models.TextField(blank=True, null=True)
    practitioner_notes = models.TextField(blank=True, null=True)
    version = models.IntegerField(default=1) # Prevent double booking
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['practitioner', 'date', 'time']
        ordering = ['-date', '-time']
        indexes = [
            models.Index(fields=['client', 'status']),
            models.Index(fields=['practitioner', 'status']),
        ]

    def __str__(self):
        return f"{self.client.get_full_name()} with {self.practitioner} on {self.date} at {self.time}"
    
class Review(models.Model):
    consultation= models.OneToOneField(Consultation, on_delete=models.CASCADE, related_name='review')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    rating = models.PositiveSmallIntegerField(choices=[(i,i) for i in range(1,6)], validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.reviewer.email} for {self.consultation}"