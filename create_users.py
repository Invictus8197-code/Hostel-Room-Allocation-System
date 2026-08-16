import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.config.settings.local')
django.setup()

from backend.apps.accounts.models import User, StudentProfile, WardenProfile
from django.contrib.auth.hashers import make_password

def create_defaults():
    # SUPERADMIN
    superadmin, created = User.objects.get_or_create(username='superadmin', defaults={
        'password': make_password('superadmin123'),
        'role': User.Role.SUPERADMIN,
        'first_name': 'System',
        'last_name': 'Superadmin'
    })
    if created:
        print("Created superadmin:superadmin123")
        
    # WARDEN
    warden, created = User.objects.get_or_create(username='warden', defaults={
        'password': make_password('warden123'),
        'role': User.Role.WARDEN,
        'first_name': 'Hostel',
        'last_name': 'Warden'
    })
    if created:
        WardenProfile.objects.get_or_create(user=warden)
        print("Created warden:warden123")
        
    # STUDENT
    student, created = User.objects.get_or_create(username='student1', defaults={
        'password': make_password('student123'),
        'role': User.Role.STUDENT,
        'first_name': 'Test',
        'last_name': 'Student'
    })
    if created:
        StudentProfile.objects.get_or_create(user=student, registration_number='M_01', gender='MALE', course_year='1')
        print("Created student1:student123")

if __name__ == '__main__':
    create_defaults()
    print("Done checking users.")
