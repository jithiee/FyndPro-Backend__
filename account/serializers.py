from rest_framework import serializers
from django.core.validators import RegexValidator
from .models import User, EmployeeProfile
from django.contrib.auth import authenticate
import re
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import password_validation

#-------------Register Serializer ---------------------
class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        min_length=6,
        error_messages={
            "min_length": "Password must be at least 6 characters long."
        }
    )
    confirm_password = serializers.CharField(
        write_only=True,
        min_length=6,
        error_messages={
            "min_length": "Confirm password must be at least 6 characters long."
        }
    )

    phone = serializers.CharField(
        required=False,
        allow_blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?\d{10,15}$',
                message="Enter a valid phone number (10–15 digits)."
            )
        ]
    )

    class Meta:
        model = User
        fields = [
            'email', 'full_name', 'latitude', 'longitude','password', 'confirm_password',
            'role', 'phone', 'location'
        ]

    # ------------VALIDATION-----------------
    def validate(self, attrs):
        """Ensure passwords match."""
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs
    
    
    # def validate_password(self, value):
    #     if len(value) < 8:
    #         raise serializers.ValidationError("Password must be at least 8 characters long.")
    #     if not re.search(r"[A-Z]", value):
    #         raise serializers.ValidationError("Password must contain at least one uppercase letter.")
    #     if not re.search(r"[a-z]", value):
    #         raise serializers.ValidationError("Password must contain at least one lowercase letter.")
    #     if not re.search(r"[0-9]", value):
    #         raise serializers.ValidationError("Password must contain at least one number.")
    #     if not re.search(r"[@$!%*#?&]", value):
    #         raise serializers.ValidationError("Password must contain at least one special character (@, $, !, %, *, #, ?, &).")
    #     return value
    
    
    # def validate_confirm_password(self, value):
    #     if len(value) < 8:
    #         raise serializers.ValidationError("Confirm password must be at least 8 characters long.")
    #     return value

    def validate_full_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Full name cannot be empty.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_location(self, value):
        if not value.strip():
            raise serializers.ValidationError("Location cannot be empty.")
        return value

    def validate_latitude(self, value):
        if value is not None and (value < -90 or value > 90):
            raise serializers.ValidationError("Latitude must be between -90 and 90.")
        return value

    def validate_longitude(self, value):
        if value is not None and (value < -180 or value > 180):
            raise serializers.ValidationError("Longitude must be between -180 and 180.")
        return value
   
    # --------- CREATE USER--------------------
    def create(self, validated_data):
        validated_data.pop('confirm_password')  # remove before creating user
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        
        # Create employee profile if role is employee
        if user.role == 'employee':
            EmployeeProfile.objects.create(user=user)
        return user
    
#------------ VerifyOTP Serializer-------------
class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate(self, attrs):
        email = attrs.get("email")
        otp = attrs.get("otp")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        if user.is_verified:
            raise serializers.ValidationError("User already verified.")

        if not user.otp:
            raise serializers.ValidationError("No OTP found for this user. Please request a new one.")

        if user.otp != otp:
            raise serializers.ValidationError("Invalid OTP")

        user.is_verified = True
        user.is_active = True
        user.otp = None
        user.save(update_fields=['is_verified', 'is_active', 'otp'])

        return {'user': user}
    
    
#---------- Login Serializer -----------
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        # Authenticate user
        user = authenticate(username=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid email or password.")

        if not user.is_verified:
            raise serializers.ValidationError("Please verify your account using OTP.")

        if not user.is_active:
            raise serializers.ValidationError("This account is inactive. Please contact admin.")

        attrs['user'] = user
        return attrs
    
# class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
#     @classmethod
#     def get_token(cls, user):
#         token = super().get_token(user)

#         #  Add custom user data here
#         token['email'] = user.email
#         token['full_name'] = user.full_name
#         token['role'] = user.role
#         token['is_verified'] = user.is_verified

#         return token


#------------ ForgotPassword Serializer ----------------
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        return value

#-----------ResetPassword Serializer-------------------
class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, attrs):
        email = attrs.get("email")
        otp = attrs.get("otp")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        if user.otp != otp:
            raise serializers.ValidationError("Invalid OTP.")
        return attrs
    
#------------ChangePassword Serializer------------------    
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)

    def validate_new_password(self, value):
        # Optionally use Django’s built-in password validators
        password_validation.validate_password(value)
        return value
    

# ----------- User Profile Serializer -----------
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'role',
            'phone', 'location', 'latitude' , 'longitude' ,  'profile_image', 'is_verified'
        ]
        read_only_fields = ['email', 'role', 'is_verified']


#---------- Employee Profle Get the Employee Register Data -------
class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'phone', 'location', 'profile_image']


# ----------- Employee Profile Serializer -----------
class EmployeeProfileSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True) 
    average_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = EmployeeProfile
        fields = [
            'id', 'title', 'skills', 'experience',
            'hourly_rate', 'available', 'bio', 'average_rating', 'user', 
        ]
  
    

    
    
    
    










    
    
    
    
    