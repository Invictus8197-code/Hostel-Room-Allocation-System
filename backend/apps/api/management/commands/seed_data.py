import sys
from datetime import date
from django.core.management.base import BaseCommand
from django.db import transaction
from backend.apps.accounts.models import User, StudentProfile
from backend.apps.hostels.models import Hostel, Block, Floor, Room, Bed
from backend.apps.applications.models import ApplicationBatch, StudentApplication, Preference

class Command(BaseCommand):
    help = 'Seeds the database with realistic Phase 8 demo data (safe and isolated).'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding realistic Phase 8 demo data...')
        
        with transaction.atomic():
            # 1. Ensure Auth Users exist
            if not User.objects.filter(username='admin').exists():
                admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'admin')
                admin_user.role = User.Role.ADMIN
                admin_user.save()
                self.stdout.write(self.style.SUCCESS('Created ADMIN user: admin / admin'))
            
            if not User.objects.filter(username='warden').exists():
                User.objects.create_user('warden', 'warden@test.com', 'warden', role=User.Role.WARDEN)
                self.stdout.write(self.style.SUCCESS('Created WARDEN user: warden / warden'))

            # We use a strict prefix for demo to allow idempotent reruns safely
            PREFIX = "DEMO_"
            
            # 2. Create Hostels and Beds (50 beds total)
            # Boys Hostel: ~30 beds
            boys_hostel, _ = Hostel.objects.get_or_create(name=f'{PREFIX}Boys Hostel', defaults={'gender_type': Hostel.GenderType.BOYS})
            b_block, _ = Block.objects.get_or_create(hostel=boys_hostel, name='Block B1')
            b_floor, _ = Floor.objects.get_or_create(block=b_block, floor_number=1)
            
            # Create 15 Double Rooms (30 beds)
            for i in range(1, 16):
                room_num = f'B10{i}'
                is_ac = i <= 5 # First 5 are AC
                room, _ = Room.objects.get_or_create(floor=b_floor, room_number=room_num, defaults={'room_type': Room.RoomType.DOUBLE, 'is_ac': is_ac})
                Bed.objects.get_or_create(room=room, bed_number=f'{room_num}-A')
                Bed.objects.get_or_create(room=room, bed_number=f'{room_num}-B')
                
            # Girls Hostel: ~20 beds
            girls_hostel, _ = Hostel.objects.get_or_create(name=f'{PREFIX}Girls Hostel', defaults={'gender_type': Hostel.GenderType.GIRLS})
            g_block, _ = Block.objects.get_or_create(hostel=girls_hostel, name='Block G1')
            g_floor, _ = Floor.objects.get_or_create(block=g_block, floor_number=1)
            
            # Create 10 Double Rooms (20 beds)
            for i in range(1, 11):
                room_num = f'G10{i}'
                is_ac = i <= 3 # First 3 are AC
                room, _ = Room.objects.get_or_create(floor=g_floor, room_number=room_num, defaults={'room_type': Room.RoomType.DOUBLE, 'is_ac': is_ac})
                Bed.objects.get_or_create(room=room, bed_number=f'{room_num}-A')
                Bed.objects.get_or_create(room=room, bed_number=f'{room_num}-B')

            self.stdout.write(self.style.SUCCESS(f'Verified 50 beds across {boys_hostel.name} and {girls_hostel.name}.'))

            # 3. Create a Demo Batch
            batch_name = f'{PREFIX}Fall 2026 Demo'
            batch, _ = ApplicationBatch.objects.get_or_create(
                name=batch_name,
                defaults={
                    'start_date': date(2026, 9, 1),
                    'end_date': date(2027, 5, 31)
                }
            )
            
            # Create 65 Students & Applications (35 Male, 30 Female)
            student_configs = []
            for i in range(1, 36):
                student_configs.append(('MALE', i))
            for i in range(1, 31):
                student_configs.append(('FEMALE', i))
                
            for gender, idx in student_configs:
                username = f'demo_{gender.lower()}_{idx}'
                u, created = User.objects.get_or_create(username=username, defaults={
                    'email': f'{username}@example.com',
                    'role': User.Role.STUDENT,
                    'first_name': 'Demo',
                    'last_name': f'Student {gender} {idx}'
                })
                if created:
                    u.set_password('password')
                    u.save()
                
                sp, _ = StudentProfile.objects.get_or_create(
                    user=u, 
                    defaults={
                        'registration_number': f'REG_{gender}_{idx:03d}', 
                        'department': 'Engineering', 
                        'course_year': 2 if idx % 2 == 0 else 1, 
                        'gender': StudentProfile.Gender.MALE if gender == 'MALE' else StudentProfile.Gender.FEMALE
                    }
                )
                
                app, created_app = StudentApplication.objects.get_or_create(batch=batch, student=sp)
                
                if created_app:
                    # Give them some varied preferences
                    wants_ac = (idx % 3 == 0) # 1 in 3 wants AC
                    Preference.objects.create(
                        application=app, 
                        preferred_room_type=Room.RoomType.DOUBLE, 
                        preferred_ac=wants_ac, 
                        budget_tier=Preference.BudgetTier.PREMIUM if wants_ac else Preference.BudgetTier.STANDARD
                    )
            
            self.stdout.write(self.style.SUCCESS('Created/Verified 65 Student Applications (35 Male, 30 Female).'))

        self.stdout.write(self.style.SUCCESS('Phase 8 Demo Seeding Complete! Safe to run multiple times.'))
