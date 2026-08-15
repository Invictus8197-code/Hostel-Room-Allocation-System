from django.test import TestCase
from datetime import date
from django.db import transaction
from backend.apps.accounts.models import User, StudentProfile
from backend.apps.hostels.models import Hostel, Block, Floor, Room, Bed
from backend.apps.applications.models import ApplicationBatch, StudentApplication, Preference
from backend.apps.allocations.models import BedAllocation, AllocationRun
from backend.apps.allocations.services.optimizer import HostelOptimizer

class OptimizerTestCase(TestCase):
    def setUp(self):
        # Create Batches
        self.batch = ApplicationBatch.objects.create(
            name="Fall 2026",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 5, 31)
        )
        self.other_batch = ApplicationBatch.objects.create(
            name="Spring 2027",
            start_date=date(2027, 1, 1),
            end_date=date(2027, 5, 31)
        )

        # Create Hostels
        self.boys_hostel = Hostel.objects.create(name="Boys A", gender_type=Hostel.GenderType.BOYS)
        self.girls_hostel = Hostel.objects.create(name="Girls A", gender_type=Hostel.GenderType.GIRLS)

        # Create Blocks, Floors, Rooms, Beds for Boys
        self.b_block = Block.objects.create(hostel=self.boys_hostel, name="B1")
        self.b_floor = Floor.objects.create(block=self.b_block, floor_number=1)
        
        self.b_room_single_ac = Room.objects.create(floor=self.b_floor, room_number="101", room_type=Room.RoomType.SINGLE, is_ac=True)
        self.b_bed_1 = Bed.objects.create(room=self.b_room_single_ac, bed_number="A")
        
        self.b_room_double_nonac = Room.objects.create(floor=self.b_floor, room_number="102", room_type=Room.RoomType.DOUBLE, is_ac=False)
        self.b_bed_2 = Bed.objects.create(room=self.b_room_double_nonac, bed_number="A")
        self.b_bed_3 = Bed.objects.create(room=self.b_room_double_nonac, bed_number="B")

        # Create Blocks, Floors, Rooms, Beds for Girls
        self.g_block = Block.objects.create(hostel=self.girls_hostel, name="G1")
        self.g_floor = Floor.objects.create(block=self.g_block, floor_number=1)
        
        self.g_room_single_ac = Room.objects.create(floor=self.g_floor, room_number="201", room_type=Room.RoomType.SINGLE, is_ac=True)
        self.g_bed_1 = Bed.objects.create(room=self.g_room_single_ac, bed_number="A")

        # Create Students
        self.male_student_1 = self._create_student("M1", StudentProfile.Gender.MALE)
        self.male_student_2 = self._create_student("M2", StudentProfile.Gender.MALE)
        self.male_student_3 = self._create_student("M3", StudentProfile.Gender.MALE)
        self.female_student_1 = self._create_student("F1", StudentProfile.Gender.FEMALE)
        self.female_student_2 = self._create_student("F2", StudentProfile.Gender.FEMALE)
        self.other_student = self._create_student("O1", StudentProfile.Gender.OTHER)

    def _create_student(self, reg_no, gender):
        user = User.objects.create_user(username=reg_no, email=f"{reg_no}@example.com", password="pass")
        return StudentProfile.objects.create(
            user=user, 
            registration_number=reg_no, 
            department="CS",
            course_year=1,
            gender=gender
        )

    def _create_app(self, student, batch, status=StudentApplication.Status.PENDING, room_type=Room.RoomType.SINGLE, ac=True):
        app = StudentApplication.objects.create(student=student, batch=batch, status=status)
        Preference.objects.create(
            application=app,
            preferred_room_type=room_type,
            preferred_ac=ac,
            budget_tier=Preference.BudgetTier.STANDARD
        )
        return app

    def test_student_selection(self):
        # 1. PENDING included
        self._create_app(self.male_student_1, self.batch)
        
        # 2. Non-pending excluded
        self._create_app(self.male_student_2, self.batch, status=StudentApplication.Status.APPROVED)
        
        # 3. Wrong batch excluded
        self._create_app(self.male_student_3, self.other_batch)
        
        # 4. Active allocation excluded
        f1_app = self._create_app(self.female_student_1, self.batch)
        run = AllocationRun.objects.create()
        BedAllocation.objects.create(
            student=self.female_student_1,
            bed=self.g_bed_1,
            allocation_run=run,
            start_date=self.batch.start_date,
            end_date=self.batch.end_date,
            is_active=True
        )

        opt = HostelOptimizer(self.batch.id)
        opt.validate_batch()
        opt.select_eligible_students()
        
        # Only male_student_1 should be eligible
        self.assertEqual(len(opt.eligible_students), 1)
        self.assertEqual(opt.eligible_students[0].student.registration_number, "M1")

    def test_bed_selection_and_overlap(self):
        # b_bed_1 has overlapping allocation
        run = AllocationRun.objects.create()
        BedAllocation.objects.create(
            student=self.male_student_1,
            bed=self.b_bed_1,
            allocation_run=run,
            start_date=self.batch.start_date,
            end_date=self.batch.end_date,
            is_active=True
        )
        
        # b_bed_2 has non-overlapping historical allocation (ends before batch starts)
        BedAllocation.objects.create(
            student=self.male_student_2,
            bed=self.b_bed_2,
            allocation_run=run,
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            is_active=True
        )

        opt = HostelOptimizer(self.batch.id)
        opt.validate_batch()
        opt.select_available_beds()
        
        available_bed_ids = [bed.id for bed in opt.available_beds]
        self.assertNotIn(self.b_bed_1.id, available_bed_ids) # Overlapping, excluded
        self.assertIn(self.b_bed_2.id, available_bed_ids) # Historical, included
        self.assertIn(self.b_bed_3.id, available_bed_ids) # Never allocated, included

    def test_gender_constraints(self):
        # We only have MALE, FEMALE, OTHER students, and BOYS, GIRLS hostels.
        self._create_app(self.male_student_1, self.batch) # M1
        self._create_app(self.female_student_1, self.batch) # F1
        self._create_app(self.other_student, self.batch) # O1
        
        opt = HostelOptimizer(self.batch.id)
        result = opt.run()
        assignments = result['assignments']
        
        m1_bed = next((bed for app, bed in assignments if app.student == self.male_student_1), None)
        self.assertIsNotNone(m1_bed)
        self.assertEqual(m1_bed.room.floor.block.hostel.gender_type, Hostel.GenderType.BOYS)
        
        f1_bed = next((bed for app, bed in assignments if app.student == self.female_student_1), None)
        self.assertIsNotNone(f1_bed)
        self.assertEqual(f1_bed.room.floor.block.hostel.gender_type, Hostel.GenderType.GIRLS)
        
        o1_bed = next((bed for app, bed in assignments if app.student == self.other_student), None)
        self.assertIsNone(o1_bed)

    def test_preference_scoring_and_objective_priority(self):
        # There are 3 Boys beds: 1 Single-AC, 2 Double-NonAC
        # 3 Male students applying.
        
        # M1 prefers Single-AC (perfect match for bed 1 -> +15 points)
        self._create_app(self.male_student_1, self.batch, room_type=Room.RoomType.SINGLE, ac=True)
        # M2 prefers Double-NonAC (perfect match for bed 2/3 -> +15 points)
        self._create_app(self.male_student_2, self.batch, room_type=Room.RoomType.DOUBLE, ac=False)
        # M3 prefers Single-AC (match for bed 1 -> +15 points, but only 1 Single-AC bed exists)
        self._create_app(self.male_student_3, self.batch, room_type=Room.RoomType.SINGLE, ac=True)
        
        # Run optimizer
        opt = HostelOptimizer(self.batch.id)
        result = opt.run()
        
        self.assertEqual(result['allocated_count'], 3)
        self.assertEqual(len(result['assignments']), 3)
        self.assertAlmostEqual(result['fairness_score'], 30.0 / 45.0, places=4)

    def test_empty_cases(self):
        # 1. Zero students
        opt = HostelOptimizer(self.batch.id)
        result = opt.run()
        self.assertEqual(result['status'], 'OPTIMAL')
        self.assertEqual(result['allocated_count'], 0)
        
        # 2. Zero beds
        self._create_app(self.male_student_1, self.batch)
        Bed.objects.all().delete()
        
        opt2 = HostelOptimizer(self.batch.id)
        result2 = opt2.run()
        self.assertIn(result2['status'], ['OPTIMAL', 'INFEASIBLE'])
        self.assertEqual(result2['allocated_count'], 0)
