from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserRegisterSerializer , VerifyOTPSerializer , LoginSerializer ,ResetPasswordSerializer ,ForgotPasswordSerializer ,ChangePasswordSerializer , UserProfileSerializer , EmployeeProfileSerializer
from rest_framework.permissions import AllowAny , IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from . models import User , EmployeeProfile 
from . utils import send_otp_email , get_tokens_for_user
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view
from booking.models import Booking , Complaint

from helpers.ai_client import ai_chat


#----------Ai Chat Bot-----------
# @api_view(["POST"])
# def chatbot(request):
#     message = request.data.get("message", "")
#     reply = ai_chat(message)
#     return Response({"reply": reply})

@api_view(["POST"])
def chatbot(request):
    user = request.user     # logged-in user (JWT/Session)

    message = request.data.get("message", "")

    # -------------------------
    # 1️⃣ Get Basic User Info
    # -------------------------
    user_info = {
        "name": user.full_name,
        "email": user.email,
        "role": user.role,
        "phone": user.phone,
        "location": user.location,
    }

    # -------------------------
    # 2️⃣ Get Employee Profile (if role == employee)
    # -------------------------
    employee_info = None
    if user.role == "employee":
        profile = user.employee_profile
        employee_info = {
            "title": profile.title,
            "experience": profile.experience,
            "hourly_rate": float(profile.hourly_rate),
            "skills": profile.skills,
            "available": profile.available,
            "rating": profile.average_rating,
            "bio": profile.bio,
        }

    # -------------------------
    # 3️⃣ Get Client Bookings
    # -------------------------
    bookings = Booking.objects.filter(client=user).order_by("-created_at")[:5]

    booking_info = []
    for b in bookings:
        booking_info.append({
            "id": str(b.book_id),
            "employee": b.employee.user.full_name,
            "job": b.job,
            "amount": float(b.amount) if b.amount else None,
            "date": b.booking_date.strftime("%Y-%m-%d %H:%M"),
            "status": b.status,
            "is_paid": b.is_paid,
        })

    # -------------------------
    # 4️⃣ Employee appointment list (if logged-in is employee)
    # -------------------------
    employee_appointments = []
    if user.role == "employee":
        appts = Booking.objects.filter(employee=user.employee_profile).order_by("-created_at")[:5]
        for a in appts:
            employee_appointments.append({
                "id": str(a.book_id),
                "client": a.client.full_name,
                "job": a.job,
                "date": a.booking_date.strftime("%Y-%m-%d %H:%M"),
                "status": a.status,
            })

    # -------------------------
    # 5️⃣ Recent complaints
    # -------------------------
    # complaints = Complaint.objects.filter(client=user).order_by("-created_at")[:3]
    # complaint_info = [
    #     {
    #         "subject": c.subject,
    #         "status": c.status,
    #         "booking_id": str(c.booking.book_id) if c.booking else None,
    #     }
    #     for c in complaints
    # ]

    # -------------------------
    # 6️⃣ Build AI Context
    # -------------------------
    context = {
        "user_info": user_info,
        "employee_profile": employee_info,
        "recent_bookings": booking_info,
        "employee_appointments": employee_appointments,
        # "complaints": complaint_info,
    }

    final_message = (
        "Here is the authenticated user's context. "
        "Use this ONLY to help answer their question:\n\n"
        f"{context}\n\n"
        f"User message: {message}"
    )

    reply = ai_chat(final_message)

    return Response({"reply": reply})





#---------- Registeration----------------
class RegisterView(APIView):
    
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Register a new user (Client or Employee).",
        request_body=UserRegisterSerializer,
        responses={
            201: openapi.Response('User registered successfully'),
            400: openapi.Response('Bad Request')
        }
    )
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            send_otp_email(user)
            return Response(
                {
                    "status": "success",
                    "message": "Registration successful! Please check your email for the OTP to verify your account.",
                    "data": {
                        "id": user.id,
                        "email": user.email,
                        "full_name": user.full_name,
                        "role": user.role,
                        "phone": user.phone,
                        "location": user.location,
                        "latitude": user.latitude , 
                        "longitude": user.longitude ,
                        
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            {
                "message": "Registration failed.",
                "error": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


# -------- Verify OTP ----------
class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Verify the OTP sent to the user's email after registration.",
        request_body=VerifyOTPSerializer,
        responses={
            200: openapi.Response('OTP verified successfully. You can now login.'),
            400: openapi.Response('Invalid or expired OTP.'),
        }
    )
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            return Response(
                {"message": "OTP verified successfully. You can now log in."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------- Resend OTP ----------
class ResendOTPView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Resend OTP to user's registered email if not yet verified.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='User email address')
            },
            required=['email']
        ),
        responses={
            200: openapi.Response('New OTP sent to your email'),
            400: openapi.Response('User already verified or missing email'),
            404: openapi.Response('User not found')
        }
    )
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if user.is_verified:
            return Response({"error": "This account is already verified."}, status=status.HTTP_400_BAD_REQUEST)

        send_otp_email(user)
        return Response({"message": "A new OTP has been sent to your registered email."}, status=status.HTTP_200_OK)



# -------- Login (JWT generation) ----------
class LoginView(APIView):
    permission_classes = [AllowAny]
    
    @swagger_auto_schema(
        operation_description="Login with email and password to receive JWT tokens.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Registered email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='User password'),
            },
            required=['email', 'password']
        ),
        responses={
            200: openapi.Response('Login successful — returns JWT tokens and user details'),
            400: openapi.Response('Invalid credentials or user not verified'),
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
                user = serializer.validated_data['user']
                tokens = get_tokens_for_user(user)
                return Response({
                    "access": str(tokens['access']),
                    "refresh": str(tokens['refresh']),
                    "user": UserProfileSerializer(user).data
                }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
    
# -------- Forgot Password (Send OTP) ----------
class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Send an OTP to the user's registered email for password reset.",
        request_body=ForgotPasswordSerializer,
        responses={
            200: openapi.Response('OTP sent successfully'),
            400: openapi.Response('User not found or invalid email'),
        }
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            user = User.objects.get(email=email)
            send_otp_email(user)
            return Response({"msg": "OTP sent to your email"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------- Reset Password (Verify OTP + Set New Password) ----------
class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="Reset password after verifying OTP.",
        request_body=ResetPasswordSerializer,
        responses={
            200: openapi.Response('Password reset successfully'),
            400: openapi.Response('Invalid OTP or data'),
        }
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            new_password = serializer.validated_data["new_password"]
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.otp = None
            user.save()
            return Response({"msg": "Password reset successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
# -------- Change Password --------------------
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Change password for an authenticated user.",
        request_body=ChangePasswordSerializer,
        responses={
            200: openapi.Response('Password changed successfully'),
            400: openapi.Response('Invalid old password or bad request'),
            401: openapi.Response('Authentication credentials were not provided'),
        }
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            old_password = serializer.validated_data['old_password']
            new_password = serializer.validated_data['new_password']

            # Verify old password
            if not user.check_password(old_password):
                return Response(
                    {"error": "Old password is incorrect"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Set and save new password
            user.set_password(new_password)
            user.save()

            return Response(
                {"msg": "Password changed successfully"},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
   

# ----------- USER PROFILE API VIEW -----------
class UserProfileAPIView(APIView):
    """
    Handles viewing and updating basic user information.
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Get User Profile",
        operation_description="Retrieve the authenticated user's profile details.",
        responses={200: UserProfileSerializer()}
    )
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_summary="Update User Profile",
        operation_description="Partially update user's profile (full_name, phone, location, etc.)",
        request_body=UserProfileSerializer,
        responses={
            200: openapi.Response("Profile updated successfully", UserProfileSerializer),
            400: "Invalid data provided"
        }
    )
    def put(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Profile updated successfully.",
                "user": serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ----------- EMPLOYEE PROFILE API VIEW -----------
class EmployeeProfileAPIView(APIView):
    """
    Handles viewing and updating both user & employee profile info.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser] 
    
    @swagger_auto_schema(
        operation_summary="Get Employee Profile",
        operation_description="Retrieve the authenticated employee's profile, including user details and employee-specific information.",
        responses={
            200: openapi.Response(
                description="Employee profile data retrieved successfully",
                schema=EmployeeProfileSerializer()
            ),
            403: "Only employees can view this profile.",
            404: "Employee profile not found."
        }
    )
    def get(self, request):
        if request.user.role != 'employee':
            return Response({"error": "Only employees can view this profile."},
                            status=status.HTTP_403_FORBIDDEN)

        try:
            employee_profile = request.user.employee_profile
        except EmployeeProfile.DoesNotExist:
            return Response({"error": "Employee profile not found."},
                            status=status.HTTP_404_NOT_FOUND)

        user_data = UserProfileSerializer(request.user).data
        employee_data = EmployeeProfileSerializer(employee_profile).data

        return Response({
            **user_data,
            "employee_profile": employee_data
        }, status=status.HTTP_200_OK)


    @swagger_auto_schema(
        operation_summary="Update Employee Profile",
        operation_description="""
        Allows employees to update both user fields (e.g., full_name, phone, location, profile_image) 
        and employee fields (e.g., title, skills, experience, hourly_rate, available, bio).
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'full_name': openapi.Schema(type=openapi.TYPE_STRING, description="Employee full name"),
                'phone': openapi.Schema(type=openapi.TYPE_STRING, description="Employee phone number"),
                'location': openapi.Schema(type=openapi.TYPE_STRING, description="Employee location"),
                'profile_image': openapi.Schema(type=openapi.TYPE_STRING, description="Profile image URL or file"),
                'title': openapi.Schema(type=openapi.TYPE_STRING, description="Job title"),
                'skills': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_INTEGER), description="List of skill IDs"),
                'experience': openapi.Schema(type=openapi.TYPE_INTEGER, description="Years of experience"),
                'hourly_rate': openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_FLOAT, description="Hourly rate"),
                'available': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Availability status"),
                'bio': openapi.Schema(type=openapi.TYPE_STRING, description="Short bio or description"),
            },
        ),
        responses={
            200: openapi.Response(
                description="Profile updated successfully",
                schema=EmployeeProfileSerializer()
            ),
            400: "Validation error",
            403: "Only employees can update this profile.",
            404: "Employee profile not found."
        }
    )
    def put(self, request):
        if request.user.role != 'employee':
            return Response({"error": "Only employees can update this profile."},
                            status=status.HTTP_403_FORBIDDEN)

        try:
            employee_profile = request.user.employee_profile
        except EmployeeProfile.DoesNotExist:
            return Response({"error": "Employee profile not found."},
                            status=status.HTTP_404_NOT_FOUND)

        # Split data for user and employee models
        user_fields = ['full_name', 'phone', 'location', 'profile_image']
        employee_fields = [
            'title', 'skills', 'experience', 'hourly_rate', 'available', 'bio'
        ]

        user_data = {field: request.data.get(field) for field in user_fields if field in request.data}
        employee_data = {field: request.data.get(field) for field in employee_fields if field in request.data}
        print(user_data, 'uuuuuuuuuuuuuuu')
        print(employee_data , 'eeeeeeeeeeeeeee')
        user_serializer = UserProfileSerializer(request.user, data=user_data, partial=True)
        employee_serializer = EmployeeProfileSerializer(employee_profile, data=employee_data, partial=True)

        if user_serializer.is_valid() and employee_serializer.is_valid():
            user_serializer.save()
            employee_serializer.save()

            return Response({
                "message": "Profile updated successfully.",
                "user": user_serializer.data,
                "employee_profile": employee_serializer.data
            }, status=status.HTTP_200_OK)

        # Merge validation errors from both serializers
        errors = {**user_serializer.errors, **employee_serializer.errors}
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)
    
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
 
    
    
