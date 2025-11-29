import uuid
from django.db import models
from account.models import User, EmployeeProfile

# --------- Booking Model ---------
class Booking(models.Model):
    """
      A client can book an employee (professional)
    """
    book_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    IN_PROGRESS = "in_Progress"
    CANCELED = "canceled"
    INCOMPLETED = "incompleted"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (CANCELED, "Canceled"),
        (CONFIRMED, "Confirmed"),     
        (IN_PROGRESS, "In_Progress"),     
        (COMPLETED, "Completed"),
        (INCOMPLETED, "Incompleted"),
    ]

    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name="appointments")
    booking_date = models.DateTimeField()
    job = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    def __str__(self):
        return f"Booking {self.book_id} - {self.client.full_name} → {self.employee.user.full_name} ({self.status})"

    class Meta:
        ordering = ['-created_at']



# --------- Complaint Model ---------
class Complaint(models.Model):
    """
    A client can file a complaint about an employee,
    linked to a specific booking, with optional attachments.
    Admin can review and resolve the complaint.
    """

    # ---- Status options ----
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    REJECTED = "rejected"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (UNDER_REVIEW, "Under Review"),
        (RESOLVED, "Resolved"),
        (REJECTED, "Rejected"),
    ]

    client = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="complaints_filed"
    )
    employee = models.ForeignKey(
        EmployeeProfile, on_delete=models.CASCADE, related_name="complaints_received"
    )
    booking = models.ForeignKey(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='complaints')

    subject = models.CharField(max_length=200)
    description = models.TextField()
    attachment = models.FileField(upload_to='complaint_attachments/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    admin_response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Complaint {self.id} - {self.client.full_name} → {self.employee.user.full_name} ({self.status})"

    class Meta:
        ordering = ['-created_at']
