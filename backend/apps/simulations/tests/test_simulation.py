from django.test import TestCase
from backend.apps.accounts.models import User
from datetime import date
from backend.apps.accounts.models import StudentProfile
from backend.apps.hostels.models import Hostel, Block, Floor, Room, Bed
from backend.apps.applications.models import ApplicationBatch, StudentApplication, Preference
from backend.apps.allocations.models import AllocationRun, BedAllocation
from backend.apps.simulations.services.simulation_service import SimulationService

class SimulationServiceTestCase(TestCase):
    def setUp(self):
        # 1. Hostels
        self.boys_hostel = Hostel.objects.create(name="Boys Hostel", gender_type=Hostel.GenderType.BOYS)
        self.girls_hostel = Hostel.objects.create(name="Girls Hostel", gender_type=Hostel.GenderType.GIRLS)

        b_block = Block.objects.create(hostel=self.boys_hostel, name="B-Block")
        b_floor = Floor.objects.create(block=b_block, floor_number=1)
        self.b_room = Room.objects.create(floor=b_floor, room_number="101", room_type=Room.RoomType.DOUBLE, is_ac=True)
        self.b_bed1 = Bed.objects.create(room=self.b_room, bed_number="1")
        self.b_bed2 = Bed.objects.create(room=self.b_room, bed_number="2")

        g_block = Block.objects.create(hostel=self.girls_hostel, name="G-Block")
        g_floor = Floor.objects.create(block=g_block, floor_number=1)
        self.g_room = Room.objects.create(floor=g_floor, room_number="101", room_type=Room.RoomType.SINGLE, is_ac=False)
        self.g_bed1 = Bed.objects.create(room=self.g_room, bed_number="1")

        # 2. Batch
        self.batch = ApplicationBatch.objects.create(
            name="Fall 2026",
            start_date=date(2026, 9, 1),
            end_date=date(2027, 5, 31)
        )

        # 3. Students & Applications
        u1 = User.objects.create_user(username="boy1")
        self.s_boy1 = StudentProfile.objects.create(user=u1, registration_number="B1", gender=StudentProfile.Gender.MALE, course_year=1, department="CS")
        self.app_boy1 = StudentApplication.objects.create(batch=self.batch, student=self.s_boy1, status=StudentApplication.Status.PENDING)
        Preference.objects.create(application=self.app_boy1, preferred_room_type=Room.RoomType.DOUBLE, preferred_ac=True)

        u2 = User.objects.create_user(username="boy2")
        self.s_boy2 = StudentProfile.objects.create(user=u2, registration_number="B2", gender=StudentProfile.Gender.MALE, course_year=1, department="CS")
        self.app_boy2 = StudentApplication.objects.create(batch=self.batch, student=self.s_boy2, status=StudentApplication.Status.PENDING)
        
        u3 = User.objects.create_user(username="girl1")
        self.s_girl1 = StudentProfile.objects.create(user=u3, registration_number="G1", gender=StudentProfile.Gender.FEMALE, course_year=1, department="CS")
        self.app_girl1 = StudentApplication.objects.create(batch=self.batch, student=self.s_girl1, status=StudentApplication.Status.PENDING)

    def _get_db_state(self):
        return {
            'alloc_runs': AllocationRun.objects.count(),
            'bed_allocs': BedAllocation.objects.count(),
            'app_statuses': list(StudentApplication.objects.values_list('id', 'status')),
            'beds': Bed.objects.count(),
            'prefs': list(Preference.objects.values_list('id', 'preferred_room_type', 'preferred_ac')),
            'hostels': Hostel.objects.count(),
            'rooms': Room.objects.count()
        }

    def _assert_db_untouched(self, initial_state):
        current_state = self._get_db_state()
        self.assertEqual(initial_state, current_state, "Database state was modified during simulation!")

    def test_basic_simulation_empty_scenario(self):
        initial_state = self._get_db_state()
        
        result = SimulationService.run_simulation(self.batch.id, {})
        
        # 3 students, 3 beds total (2 boys, 1 girl) -> All should be allocated
        self.assertEqual(result['simulated']['allocated'], 3)
        self.assertEqual(result['simulated']['unallocated'], 0)
        self.assertEqual(result['simulated']['occupancy_rate'], 1.0)
        self.assertEqual(result['difference']['allocated'], 3)
        
        self._assert_db_untouched(initial_state)

    def test_unavailable_beds_scenario(self):
        initial_state = self._get_db_state()
        
        # Make one boy's bed unavailable
        scenario = {'unavailable_bed_ids': [self.b_bed1.id]}
        result = SimulationService.run_simulation(self.batch.id, scenario)
        
        # Now there is only 1 boy's bed available for 2 boys. 
        # So 1 boy allocated, 1 unallocated. Girl still gets her 1 bed.
        # Total allocated = 2
        self.assertEqual(result['simulated']['allocated'], 2)
        self.assertEqual(result['simulated']['unallocated'], 1)
        
        # Ensure the unavailable bed is NOT in assignments
        for assignment in result['allocation']['student_bed_assignments']:
            self.assertNotEqual(assignment['bed_id'], self.b_bed1.id)
            
        self._assert_db_untouched(initial_state)

    def test_student_subset_scenario(self):
        initial_state = self._get_db_state()
        
        # Only simulate for boy1 and girl1
        scenario = {'student_ids': [self.s_boy1.id, self.s_girl1.id]}
        result = SimulationService.run_simulation(self.batch.id, scenario)
        
        self.assertEqual(result['simulated']['allocated'], 2)
        self.assertEqual(result['simulated']['unallocated'], 0)
        
        assigned_student_ids = [a['student_id'] for a in result['allocation']['student_bed_assignments']]
        self.assertIn(self.s_boy1.id, assigned_student_ids)
        self.assertIn(self.s_girl1.id, assigned_student_ids)
        self.assertNotIn(self.s_boy2.id, assigned_student_ids)
        
        self._assert_db_untouched(initial_state)

    def test_student_subset_invalid_batch(self):
        # Provide a student ID that does not exist in the batch (e.g. 9999)
        scenario = {'student_ids': [9999]}
        with self.assertRaises(ValueError) as cm:
            SimulationService.run_simulation(self.batch.id, scenario)
        self.assertIn("do not belong to the requested batch", str(cm.exception))

    def test_preference_overrides(self):
        initial_state = self._get_db_state()
        
        # boy1 prefers DOUBLE, AC. 
        # Let's override girl1 to prefer SINGLE (she has no preference initially in DB).
        # And boy2 override to prefer SINGLE (which is impossible since boys only get boys hostel with double).
        scenario = {
            'preference_overrides': {
                self.s_girl1.id: {'preferred_room_type': Room.RoomType.SINGLE},
                self.s_boy2.id: {'preferred_room_type': Room.RoomType.SINGLE}
            }
        }
        
        result = SimulationService.run_simulation(self.batch.id, scenario)
        
        self.assertEqual(result['simulated']['allocated'], 3)
        
        # We also assert DB untouched, ensuring preferences were not mutated in DB
        self._assert_db_untouched(initial_state)

    def test_gender_isolation(self):
        initial_state = self._get_db_state()
        
        # Test that boys don't get girls beds even if desperate
        # Add 10 boys. There are only 2 boy beds and 1 girl bed.
        # They should NOT be assigned to the girl bed.
        for i in range(10):
            u = User.objects.create_user(username=f"xtraboy{i}")
            sp = StudentProfile.objects.create(user=u, registration_number=f"XB{i}", gender=StudentProfile.Gender.MALE, course_year=1, department="CS")
            StudentApplication.objects.create(batch=self.batch, student=sp, status=StudentApplication.Status.PENDING)
            
        initial_state = self._get_db_state() # Update baseline state
        
        result = SimulationService.run_simulation(self.batch.id, {})
        
        # Only 2 boys and 1 girl allocated. The extra 10 boys remain unallocated.
        # Total allocated: 3
        self.assertEqual(result['simulated']['allocated'], 3)
        self.assertTrue(result['simulated']['unallocated'] >= 10)
        
        # Verify assignments
        g_bed_assigned_to = None
        for a in result['allocation']['student_bed_assignments']:
            if a['bed_id'] == self.g_bed1.id:
                g_bed_assigned_to = a['student_id']
                
        # Must be assigned to girl1, not any of the boys
        self.assertEqual(g_bed_assigned_to, self.s_girl1.id)

        self._assert_db_untouched(initial_state)
