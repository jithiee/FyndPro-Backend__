import random
from django.conf import settings
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken

#----OTP Genreate-------
def generate_otp():
    return str(random.randint(100000, 999999)).zfill(6)


def send_otp_email(user):
    otp = generate_otp()
    user.otp = otp
    user.save(update_fields=['otp'])

    subject = "Your OTP Code"
    message = f"Hello {getattr(user, 'full_name', user.email)},\n\nYour OTP code is: {otp}\n\nIt is valid for a short time."
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER)
    recipient_list = [user.email]

    # will raise if failure unless fail_silently=True
    send_mail(subject, message, from_email, recipient_list, fail_silently=False)
    return otp

#--------JWT token Generate----------
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
