from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = 'STUDENT', 'Student'
        WARDEN = 'WARDEN', 'Warden'
        ADMIN = 'ADMIN', 'Admin'
        
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        db_index=True
    )

    def __str__(self):
        return self.username


class StudentProfile(models.Model):
    class Gender(models.TextChoices):
        MALE = 'MALE', 'Male'
        FEMALE = 'FEMALE', 'Female'
        OTHER = 'OTHER', 'Other'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    registration_number = models.CharField(max_length=50, unique=True, db_index=True)
    department = models.CharField(max_length=100)
    course_year = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=Gender.choices)

    def __str__(self):
        return f"{self.registration_number} - {self.user.get_full_name()}"
