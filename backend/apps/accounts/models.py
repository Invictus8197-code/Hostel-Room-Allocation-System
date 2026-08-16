from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = 'STUDENT', 'Student'
        WARDEN = 'WARDEN', 'Warden'
        ADMIN = 'ADMIN', 'Admin'
        SUPERADMIN = 'SUPERADMIN', 'Superadmin'
        
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        db_index=True
    )

    def __str__(self):
        return self.username


class WardenProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='warden_profile')
    assigned_hostels = models.ManyToManyField('hostels.Hostel', blank=True, related_name='assigned_wardens')

    def clean(self):
        if self.pk and self.assigned_hostels.count() > 5:
            raise ValidationError("A Warden cannot be assigned more than 5 hostels.")

    def __str__(self):
        return f"Warden: {self.user.get_full_name() or self.user.username}"


class StudentProfile(models.Model):
    class Gender(models.TextChoices):
        MALE = 'MALE', 'Male'
        FEMALE = 'FEMALE', 'Female'
        OTHER = 'OTHER', 'Other'

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        COMPLETED = 'COMPLETED', 'Completed'
        LEFT_COLLEGE = 'LEFT_COLLEGE', 'Left College'
        ARCHIVED = 'ARCHIVED', 'Archived'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    registration_number = models.CharField(max_length=50, unique=True, db_index=True)
    department = models.CharField(max_length=100)
    course_year = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=Gender.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)

    def save(self, *args, **kwargs):
        if self.pk:
            old_instance = StudentProfile.objects.get(pk=self.pk)
            if old_instance.status == self.Status.ACTIVE and self.status in [self.Status.COMPLETED, self.Status.LEFT_COLLEGE]:
                # Deactivate all active allocations when entering a terminal state
                from backend.apps.allocations.models import BedAllocation
                BedAllocation.objects.filter(student=self, is_active=True).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.registration_number} - {self.user.get_full_name()}"
