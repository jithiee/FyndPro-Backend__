# account/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator


# --------- Custom User Manager ---------
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("Users must have an email address"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(email, password, **extra_fields)


# --------- Custom User Model ---------
class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=100)

    ROLE_CHOICES = (
        ('client', 'Client'),
        ('employee', 'Employee'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    phone = models.CharField(max_length=15, blank=True, null=True)
    # Add coordinates for map-based features
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True, null=True,
        help_text="Latitude (e.g. 10.5276)"
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, blank=True, null=True,
        help_text="Longitude (e.g. 76.2144)"
    )
    location = models.CharField(max_length=255, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    otp = models.CharField(max_length=6, blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name', 'role']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.full_name} ({self.email})"



# --------- Employee Profile ---------
class EmployeeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    title = models.CharField(max_length=100, blank=True, null=True)
    experience = models.PositiveIntegerField(default=0)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    available = models.BooleanField(default=True)
    bio = models.TextField(blank=True, null=True)
    skills = models.JSONField(default=list, blank=True) 

    def __str__(self):
        return f"{self.user.full_name} - {self.title or 'No Title'}"
    
    @property
    def average_rating(self):
        from django.db.models import Avg
        result = self.user.employee_ratings.aggregate(avg_rating=Avg('rating'))
        return round(result['avg_rating'] or 0, 2)
    

# --------- Employee Review (Client → Employee) ---------
class EmployeeReview(models.Model):
    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='employee_ratings'  # connects to EmployeeProfile.average_rating
    )
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='client_reviews'  # who gave the rating
    )
    rating = models.PositiveSmallIntegerField(validators=[
            MinValueValidator(1, message="Rating must be at least 1."),
            MaxValueValidator(5, message="Rating cannot exceed 5.")
        ]) 
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('employee', 'client')  # prevent duplicate reviews
        ordering = ['-created_at'] 

    def __str__(self):
        return f"{self.client.full_name} → {self.employee.full_name} ({self.rating})"
    
    

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
