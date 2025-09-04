from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.conf import settings


class CustomUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', 'doctor')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return super().create_superuser(username, email, password, **extra_fields)


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='patient')

    # extra fields for patient
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    
    # extra fields for doctor
    specialization = models.CharField(max_length=100, null=True, blank=True)
    qualification = models.CharField(max_length=200, null=True, blank=True)

    # NEW: profile image (optional)
    profile_image = models.ImageField(
        upload_to='profiles/', null=True, blank=True,
        help_text="Optional profile image (avatar)."
    )

    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        # ensure patients cannot be staff
        if self.role == 'patient':
            self.is_staff = False
        elif self.role == 'doctor':
            self.is_staff = True   # allow doctors to access admin
        super().save(*args, **kwargs)
    
    def get_display_name(self):
        """Return a formatted display name for the user"""
        if self.first_name and self.last_name:
            return f"Dr. {self.first_name} {self.last_name}"
        return f"Dr. {self.username}"


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='patient_appointments'
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_appointments',
        limit_choices_to={'role': 'doctor'},
        null=True,
        blank=False
    )
    date = models.DateField()
    time_slot = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField(null=True, blank=True, help_text="Reason for appointment")

    class Meta:
        unique_together = ('doctor', 'date', 'time_slot')  # Prevent double-booking for same doctor

    def __str__(self):
        doctor_name = self.doctor.get_display_name() if self.doctor else "No Doctor"
        return f"{self.user.username} with {doctor_name} - {self.date} {self.time_slot} ({self.status})"


class ContactSubmission(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True)
    mobile = models.CharField(max_length=20)
    email = models.EmailField()
    message = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email}) - {self.submitted_at.date()}"