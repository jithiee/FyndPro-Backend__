from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "book_id",
        "client",
        "employee",
        "booking_date",
        "job",
        "amount",
        "is_paid",
        "status",
        "is_completed",
        "created_at",
    )

    list_filter = ("status", "is_paid", "is_completed", "created_at")

    search_fields = (
        "book_id",
        "client__full_name",
        "employee__user__full_name",
        "job",
    )

    readonly_fields = ("book_id", "created_at")

    ordering = ("-created_at",)
