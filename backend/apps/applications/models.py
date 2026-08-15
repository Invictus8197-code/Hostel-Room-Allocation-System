from django.db import models
from django.core.exceptions import ValidationError
from backend.apps.accounts.models import StudentProfile
from backend.apps.hostels.models import Room

class ApplicationBatch(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True, db_index=True)

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be earlier than start date.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class StudentApplication(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        ALLOCATED = 'ALLOCATED', 'Allocated'
        REJECTED = 'REJECTED', 'Rejected'

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='applications')
    batch = models.ForeignKey(ApplicationBatch, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'batch'], name='unique_application_per_batch')
        ]

    def __str__(self):
        return f"{self.student.registration_number} - {self.batch.name} ({self.status})"


class Preference(models.Model):
    class BudgetTier(models.TextChoices):
        STANDARD = 'STANDARD', 'Standard'
        PREMIUM = 'PREMIUM', 'Premium'

    application = models.OneToOneField(StudentApplication, on_delete=models.CASCADE, related_name='preference')
    preferred_room_type = models.CharField(max_length=10, choices=Room.RoomType.choices)
    preferred_ac = models.BooleanField(null=True, blank=True)
    budget_tier = models.CharField(max_length=20, choices=BudgetTier.choices)
    roommate_requests = models.ManyToManyField(StudentProfile, blank=True, related_name='requested_by')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # We can't access m2m fields before saving, so roommate self-request validation 
        # is typically handled in forms/serializers or a custom m2m_changed signal/save method logic.
        pass

    def __str__(self):
        return f"Preferences for {self.application.student.registration_number}"
