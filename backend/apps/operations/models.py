from django.db import models
from backend.apps.accounts.models import StudentProfile
from backend.apps.hostels.models import Hostel

class Complaint(models.Model):
    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        IN_REVIEW = 'IN_REVIEW', 'In Review'
        RESOLVED = 'RESOLVED', 'Resolved'

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='complaints')
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name='complaints')
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    resolution = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.student.registration_number} ({self.status})"


class Notice(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    # JSON field for target roles (e.g., ["STUDENT", "WARDEN"])
    target_roles = models.JSONField(default=list, blank=True)
    
    # Target specific hostels (empty means system-wide if role matches)
    hostels = models.ManyToManyField(Hostel, blank=True, related_name='notices')
    
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
