from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager

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

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=50, choices=[('client', 'Client'), ('practitioner', 'Practitioner')])
    phone = models.CharField(max_length=20, null=True, blank=True)

    def __str__(self):
        return f"{self.user.email}- {self.role}"


class Specialty(models.Model):
    name= models.CharField(max_length=200)
    description= models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Practitioner(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='practitioner')
    bio = models.TextField(blank=True, null=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    specialties = models.ManyToManyField(Specialty)

    def __str__(self):
        return self.user.email

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

    def __str__(self):
        return f"{self.practitioner.user.email}-{self.get_day_of_week_display()}"

class Consultation(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='consultations')
    practitioner = models.ForeignKey(Practitioner, on_delete=models.CASCADE, related_name='consultations')
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=50, choices=[('booked','Booked'),('completed','Completed'),('cancelled','Cancelled')])

    def __str__(self):
        return f"{self.client.email} with {self.practitioner.user.email}"
    
class Review(models.Model):
    consultation= models.OneToOneField(Consultation, on_delete=models.CASCADE, related_name='review')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(choices=[(1,1), (2,2), (3,3), (4,4), (5,5)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.reviewer.email} for {self.consultation}"