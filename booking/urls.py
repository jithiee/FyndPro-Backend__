from django.urls import path
from .views import (
    NearbyEmployeesView,
    GetEmployeeByIdAPIView,
    CreateBookingAPIView,
    EmployeeBookingListAPIView,
    ClientBookingListAPIView,
    BookingStatusUpdateAPIView
    
)

urlpatterns = [
    path("nearby/", NearbyEmployeesView.as_view(), name="nearby-employees"),
    path("employee/<int:user_id>/", GetEmployeeByIdAPIView.as_view(), name="get-user-by-id"),
    
    path("create/", CreateBookingAPIView.as_view(), name="create-booking"),
    path("client/", ClientBookingListAPIView.as_view(), name="client-bookings"),
    path("employee/", EmployeeBookingListAPIView.as_view(), name="employee-bookings"),
    path("update/<uuid:book_id>/", BookingStatusUpdateAPIView.as_view(), name="update-booking-status"),
]
