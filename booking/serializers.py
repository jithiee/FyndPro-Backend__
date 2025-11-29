from rest_framework import serializers
from django.contrib.auth import get_user_model
from account.serializers import EmployeeProfileSerializer 
from .models import Booking 
from account.models import EmployeeProfile, User
from datetime import date, timedelta

User = get_user_model()

class NearbyEmployeeSerializer(serializers.ModelSerializer):
    employee_profile = EmployeeProfileSerializer(read_only=True)
    distance_km = serializers.FloatField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "full_name", "email", "location",
            "latitude", "longitude", "distance_km", 'profile_image' ,
            "employee_profile"
        ]


#-------- Fetch Id  With Employee  --------------------
class UserWithEmployeeSerializer(serializers.ModelSerializer):
    employee_profile = EmployeeProfileSerializer(read_only=True)
   
    class Meta:
        model = User
        fields = [
            "id", "email", "full_name", "role", "phone",
            "location", "latitude", "longitude", "profile_image",
            "employee_profile",  
        ]



class BookingCreateSerializer(serializers.ModelSerializer):
    employee_id = serializers.IntegerField(write_only=True)
    employee = EmployeeProfileSerializer(read_only=True)  

    class Meta:
        model = Booking
        fields = [  "book_id" , "booking_date", "job", "employee_id" , "employee" ]

    def validate_booking_date(self, value):
        # Convert datetime → date
        booking_date = value.date()
        today = date.today()

        # ---- 1. Past date check ----
        if booking_date < today:
            raise serializers.ValidationError(
                "Booking date cannot be in the past."
            )

        # ---- 3. Cannot be beyond 7 days ahead ----
        if booking_date > today + timedelta(days=7):
            raise serializers.ValidationError(
                "Booking date must be within the next 7 days."
            )

        return value

    def validate_employee_id(self, value):
        if not EmployeeProfile.objects.filter(id=value).exists():
            raise serializers.ValidationError("Employee does not exist.")
        return value

    def create(self, validated_data):
        request = self.context["request"]
        client = request.user

        employee_id = validated_data.pop("employee_id")
        employee = EmployeeProfile.objects.get(id=employee_id)

        # employee.available = False
        employee.save()

        return Booking.objects.create(
            client=client,
            employee=employee,
            status=Booking.PENDING,
            **validated_data
        )

class BookingDetailSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.full_name", read_only=True)
    employee_name = serializers.CharField(source="employee.user.full_name", read_only=True)
    employee_user = UserWithEmployeeSerializer(source="employee.user", read_only=True)
    client_user = UserWithEmployeeSerializer(source="client", read_only=True)


    class Meta:
        model = Booking
        fields = [
        
            "book_id",
            "booking_date",
            "job",
            "client",
            "client_name",
            "employee",
            "employee_name",
            "employee_user",   
            "status",
            "is_completed",
            "is_paid",
            "amount",
            "created_at",
            "client_user", 
        ]




class BookingStatusUpdateSerializer(serializers.ModelSerializer):
    working_hours = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False
    )

    class Meta:
        model = Booking
        fields = ["status", "working_hours"]

    def update(self, instance, validated_data):
        status = validated_data.get("status")
        working_hours = validated_data.get("working_hours")

        # If job is completed, calculate amount
        if status == Booking.COMPLETED:
            if working_hours is None:
                raise serializers.ValidationError(
                    {"working_hours": "Working hours are required to complete the job."}
                )

            rate = instance.employee.hourly_rate
            instance.amount = float(rate) * float(working_hours)
            instance.is_paid = True
            instance.is_completed = True

        # Update status only
        instance.status = status
        instance.save(update_fields=["status", "amount", "is_paid", "is_completed"])

        return instance
