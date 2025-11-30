from django.urls import path
from .views import RegisterView , VerifyOTPView , ResendOTPView , LoginView ,ForgotPasswordView , ResetPasswordView ,ChangePasswordView , UserProfileAPIView , EmployeeProfileAPIView , chatbot
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    
    #------Ai bot-----
    path("chatbot/", chatbot),
    
    #-------Auth----------
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('auth/resend-otp/', ResendOTPView.as_view(), name='resend_otp'),
    path('auth/login/', LoginView.as_view(), name='token_obtain_pair'),
    
    path("apitoken/", TokenObtainPairView.as_view()),
    path("refreshtoken/", TokenRefreshView.as_view()),
    
    path('auth/forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('auth/reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change_password'),
    #-----Profile---------
    path('user/profile/', UserProfileAPIView.as_view(), name='user-profile'),
    path('employee/profile/', EmployeeProfileAPIView.as_view(), name='employee-profile'),
]
