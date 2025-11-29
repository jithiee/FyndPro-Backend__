from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated , AllowAny
from rest_framework import generics, permissions, status
from django.contrib.auth import get_user_model
from django.db.models import F
from math import radians, sin, cos, sqrt, atan2
# from rest_framework import status
from .serializers import (
    NearbyEmployeeSerializer,
    UserWithEmployeeSerializer,
    BookingCreateSerializer,
    BookingDetailSerializer,
    BookingStatusUpdateSerializer
)
from .models import Booking

User = get_user_model()


# Haversine formula to calculate distance
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # KM
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)

    a = (sin(d_lat/2) ** 2 +
         cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon/2) ** 2)

    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


class NearbyEmployeesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        if not user.latitude or not user.longitude:
            return Response({"error": "Your location is not set"}, status=400)

        employees = User.objects.filter(role="employee")

        # Store employee instances so serializer works
        results = []

        for emp in employees:
            if emp.latitude and emp.longitude:
                distance = calculate_distance(
                    float(user.latitude),
                    float(user.longitude),
                    float(emp.latitude),
                    float(emp.longitude)
                )

                if distance <= 50:
                    emp.distance_km = round(distance, 2)  # attach value to instance
                    results.append(emp)

        serializer = NearbyEmployeeSerializer(results, many=True)
        return Response(serializer.data)


class GetEmployeeByIdAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UserWithEmployeeSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)



# ---------- Create Booking (Client Only) ----------
class CreateBookingAPIView(generics.CreateAPIView):
    serializer_class = BookingCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        return {"request": self.request}   

    def post(self, request, *args, **kwargs):
        if request.user.role != "client":
            return Response({"error": "Only clients can make bookings."}, status=403)

        return super().post(request, *args, **kwargs)



# ---------- Employee View Their Bookings ----------
class EmployeeBookingListAPIView(generics.ListAPIView):
    serializer_class = BookingDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role != "employee":
            return Booking.objects.none()
        return Booking.objects.filter(employee=user.employee_profile)


# ---------- Client View Their Bookings ----------
class ClientBookingListAPIView(generics.ListAPIView):
    serializer_class = BookingDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Booking.objects.filter(client=self.request.user)
    


# ---------- Employee Update Booking Status ----------
class BookingStatusUpdateAPIView(generics.UpdateAPIView):
    queryset = Booking.objects.all()
    serializer_class = BookingStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "book_id"

    def patch(self, request, *args, **kwargs):
        booking = self.get_object()
        employee_profile = booking.employee  # EmployeeProfile instance

        # ---------- Ensure the request user is the correct employee ----------
        if request.user.role != "employee" or employee_profile.user != request.user:
            return Response({"error": "Not alloweddddddd"}, status=status.HTTP_403_FORBIDDEN)

        # ---------- Update booking using serializer ----------
        response = super().patch(request, *args, **kwargs)

        # Refresh updated booking instance
        booking.refresh_from_db()

        return response
