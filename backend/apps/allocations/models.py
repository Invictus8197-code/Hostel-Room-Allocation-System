from django.db import models
from django.core.exceptions import ValidationError
from backend.apps.accounts.models import StudentProfile
from backend.apps.hostels.models import Bed

class AllocationRun(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        APPROVED = 'APPROVED', 'Approved'
        COMMITTED = 'COMMITTED', 'Committed'

    run_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    fairness_score = models.FloatField(null=True, blank=True)
    summary_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Run {self.id} on {self.run_date.strftime('%Y-%m-%d')} ({self.status})"


class BedAllocation(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.PROTECT, related_name='allocations')
    bed = models.ForeignKey(Bed, on_delete=models.PROTECT, related_name='allocations')
    allocation_run = models.ForeignKey(AllocationRun, on_delete=models.PROTECT, related_name='bed_allocations')
    
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be earlier than start date.")

        # Check for overlapping allocations for the same bed
        overlapping_bed = BedAllocation.objects.filter(
            bed=self.bed,
            is_active=True,
            start_date__lte=self.end_date,
            end_date__gte=self.start_date
        ).exclude(pk=self.pk)
        if overlapping_bed.exists():
            raise ValidationError(f"This bed is already allocated during the specified period.")

        # Check for overlapping allocations for the same student
        overlapping_student = BedAllocation.objects.filter(
            student=self.student,
            is_active=True,
            start_date__lte=self.end_date,
            end_date__gte=self.start_date
        ).exclude(pk=self.pk)
        if overlapping_student.exists():
            raise ValidationError(f"This student already has an active allocation during the specified period.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.registration_number} -> {self.bed} ({self.start_date} to {self.end_date})"
