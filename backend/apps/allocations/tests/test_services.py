from django.test import TestCase
from datetime import date
from django.db import transaction
from backend.apps.accounts.models import User, StudentProfile
from backend.apps.hostels.models import Hostel, Block, Floor, Room, Bed
from backend.apps.applications.models import ApplicationBatch, StudentApplication, Preference
from backend.apps.allocations.models import BedAllocation, AllocationRun
from backend.apps.allocations.services.allocation_service import (
    AllocationService,
    AllocationCommitService,
    InvalidBatchError,
    InvalidRunStateError,
    ConcurrencyConflictError
)

class ServicesTestCase(TestCase):
    def setUp(self):
        # Create Batch
        self.batch = ApplicationBatch.objects.create(
            name="Fall 2026",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 5, 31)
        )

        # Create Hostel
        self.boys_hostel = Hostel.objects.create(name="Boys A", gender_type=Hostel.GenderType.BOYS)
        self.b_block = Block.objects.create(hostel=self.boys_hostel, name="B1")
        self.b_floor = Floor.objects.create(block=self.b_block, floor_number=1)
        self.b_room = Room.objects.create(floor=self.b_floor, room_number="101", room_type=Room.RoomType.SINGLE, is_ac=True)
        self.bed_1 = Bed.objects.create(room=self.b_room, bed_number="A")
        self.bed_2 = Bed.objects.create(room=self.b_room, bed_number="B")

        # Create Student
        self.student_1 = self._create_student("M1", StudentProfile.Gender.MALE)
        self.app_1 = self._create_app(self.student_1, self.batch)

    def _create_student(self, reg_no, gender):
        user = User.objects.create_user(username=reg_no, email=f"{reg_no}@example.com", password="pass")
        return StudentProfile.objects.create(
            user=user, 
            registration_number=reg_no, 
            department="CS",
            course_year=1,
            gender=gender
        )

    def _create_app(self, student, batch, status=StudentApplication.Status.PENDING):
        app = StudentApplication.objects.create(student=student, batch=batch, status=status)
        Preference.objects.create(
            application=app,
            preferred_room_type=Room.RoomType.SINGLE,
            preferred_ac=True,
            budget_tier=Preference.BudgetTier.STANDARD
        )
        return app

    def test_create_draft_run_success(self):
        run = AllocationService.create_draft_run(self.batch.id)
        
        self.assertEqual(run.status, AllocationRun.Status.DRAFT)
        self.assertIn('totals', run.summary_data)
        self.assertEqual(run.summary_data['totals']['eligible_students'], 1)
        self.assertEqual(run.summary_data['totals']['allocated'], 1)
        
        # Verify BedAllocation is_active=False
        alloc = BedAllocation.objects.get(allocation_run=run)
        self.assertFalse(alloc.is_active)
        self.assertEqual(alloc.student, self.student_1)
        self.assertEqual(alloc.bed, self.bed_1)

    def test_approve_run(self):
        run = AllocationService.create_draft_run(self.batch.id)
        
        approved_run = AllocationService.approve_run(run.id)
        self.assertEqual(approved_run.status, AllocationRun.Status.APPROVED)
        
        # Cannot approve APPROVED
        with self.assertRaises(InvalidRunStateError):
            AllocationService.approve_run(approved_run.id)

    def test_commit_run_success(self):
        run = AllocationService.create_draft_run(self.batch.id)
        AllocationService.approve_run(run.id)
        
        committed_run = AllocationCommitService.commit_run(run.id)
        self.assertEqual(committed_run.status, AllocationRun.Status.COMMITTED)
        
        # BedAllocation should be active
        alloc = BedAllocation.objects.get(allocation_run=committed_run)
        self.assertTrue(alloc.is_active)
        
        # Application should be ALLOCATED
        self.app_1.refresh_from_db()
        self.assertEqual(self.app_1.status, StudentApplication.Status.ALLOCATED)

        # Cannot commit COMMITTED
        with self.assertRaises(InvalidRunStateError):
            AllocationCommitService.commit_run(committed_run.id)

    def test_invalid_transitions(self):
        run = AllocationService.create_draft_run(self.batch.id)
        
        # Cannot commit DRAFT
        with self.assertRaises(InvalidRunStateError):
            AllocationCommitService.commit_run(run.id)

    def test_concurrency_conflict(self):
        run = AllocationService.create_draft_run(self.batch.id)
        AllocationService.approve_run(run.id)
        
        # Simulate another process assigning bed_1
        student_2 = self._create_student("M2", StudentProfile.Gender.MALE)
        BedAllocation.objects.create(
            student=student_2,
            bed=self.bed_1,
            allocation_run=AllocationRun.objects.create(status=AllocationRun.Status.COMMITTED),
            start_date=self.batch.start_date,
            end_date=self.batch.end_date,
            is_active=True
        )

        with self.assertRaises(ConcurrencyConflictError):
            AllocationCommitService.commit_run(run.id)
            
        # Verify run is still APPROVED and not committed
        run.refresh_from_db()
        self.assertEqual(run.status, AllocationRun.Status.APPROVED)
        
        # Verify draft allocations are still inactive
        alloc = BedAllocation.objects.get(allocation_run=run)
        self.assertFalse(alloc.is_active)
        
        # Verify application status hasn't changed
        self.app_1.refresh_from_db()
        self.assertEqual(self.app_1.status, StudentApplication.Status.PENDING)

    def test_empty_cases(self):
        # Delete beds to force zero availability
        Bed.objects.all().delete()
        
        run = AllocationService.create_draft_run(self.batch.id)
        self.assertEqual(run.status, AllocationRun.Status.DRAFT)
        self.assertEqual(run.summary_data['totals']['allocated'], 0)
        self.assertEqual(run.summary_data['totals']['unallocated'], 1)
        
        AllocationService.approve_run(run.id)
        committed_run = AllocationCommitService.commit_run(run.id)
        self.assertEqual(committed_run.status, AllocationRun.Status.COMMITTED)
