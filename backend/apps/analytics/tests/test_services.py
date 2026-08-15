from django.test import TestCase
from datetime import date
from backend.apps.hostels.models import Hostel, Block, Floor, Room, Bed
from backend.apps.accounts.models import User, StudentProfile
from backend.apps.allocations.models import BedAllocation, AllocationRun
from backend.apps.analytics.services import AnalyticsService

class AnalyticsServiceTestCase(TestCase):
    def setUp(self):
        # 1. Create Hostels
        self.boys_hostel = Hostel.objects.create(name="Boys Hostel", gender_type=Hostel.GenderType.BOYS)
        self.girls_hostel = Hostel.objects.create(name="Girls Hostel", gender_type=Hostel.GenderType.GIRLS)
        self.empty_hostel = Hostel.objects.create(name="Empty Hostel", gender_type=Hostel.GenderType.BOYS) # No beds!

        # 2. Create Boys Blocks/Floors/Rooms/Beds
        self.b_block = Block.objects.create(hostel=self.boys_hostel, name="B1")
        self.b_floor = Floor.objects.create(block=self.b_block, floor_number=1)
        
        # Room 101: 4 Beds
        self.b_room_101 = Room.objects.create(floor=self.b_floor, room_number="101", room_type=Room.RoomType.DOUBLE, is_ac=False)
        self.b101_bed1 = Bed.objects.create(room=self.b_room_101, bed_number="A")
        self.b101_bed2 = Bed.objects.create(room=self.b_room_101, bed_number="B")
        self.b101_bed3 = Bed.objects.create(room=self.b_room_101, bed_number="C")
        self.b101_bed4 = Bed.objects.create(room=self.b_room_101, bed_number="D")

        # Room 102: 1 Bed
        self.b_room_102 = Room.objects.create(floor=self.b_floor, room_number="102", room_type=Room.RoomType.SINGLE, is_ac=True)
        self.b102_bed1 = Bed.objects.create(room=self.b_room_102, bed_number="A")

        # Room 103: Empty Room (No Beds created)
        self.b_room_103 = Room.objects.create(floor=self.b_floor, room_number="103", room_type=Room.RoomType.SINGLE, is_ac=False)

        # 3. Create Girls Blocks/Floors/Rooms/Beds
        self.g_block = Block.objects.create(hostel=self.girls_hostel, name="G1")
        self.g_floor = Floor.objects.create(block=self.g_block, floor_number=1)
        
        # Room 201: 2 Beds
        self.g_room_201 = Room.objects.create(floor=self.g_floor, room_number="201", room_type=Room.RoomType.DOUBLE, is_ac=False)
        self.g201_bed1 = Bed.objects.create(room=self.g_room_201, bed_number="A")
        self.g201_bed2 = Bed.objects.create(room=self.g_room_201, bed_number="B")

        # Analysis Period
        self.analysis_start = date(2026, 9, 1)
        self.analysis_end = date(2027, 5, 31)

    def _get_student(self, index):
        user, _ = User.objects.get_or_create(username=f"testuser_{index}", defaults={"email": f"test_{index}@test.com", "password": "pwd"})
        student, _ = StudentProfile.objects.get_or_create(
            user=user, defaults={"registration_number": f"reg_{index}", "department": "CS", "course_year": 1, "gender": StudentProfile.Gender.MALE}
        )
        return student

    def _create_allocation(self, bed, start, end, is_active=True, student_index=1, skip_clean=False):
        student = self._get_student(student_index)
        if not hasattr(self, 'allocation_run'):
            self.allocation_run = AllocationRun.objects.create(status=AllocationRun.Status.COMMITTED)
        alloc = BedAllocation(
            student=student,
            bed=bed,
            allocation_run=self.allocation_run,
            start_date=start,
            end_date=end,
            is_active=is_active
        )
        if skip_clean:
            BedAllocation.objects.bulk_create([alloc])
            return BedAllocation.objects.last()
        else:
            alloc.save()
            return alloc

    def test_zero_capacity_entity(self):
        # Empty Hostel has no beds
        res = AnalyticsService.get_hostel_utilization(self.analysis_start, self.analysis_end, hostel_id=self.empty_hostel.id)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]['total_beds'], 0)
        self.assertEqual(res[0]['occupancy_rate'], 0.0)
        self.assertEqual(res[0]['underutilized'], False) # Zero capacity should not be underutilized

    def test_room_utilization_thresholds(self):
        # Room 101 has 4 beds.
        
        # 0%
        res = AnalyticsService.get_room_utilization(self.analysis_start, self.analysis_end, room_id=self.b_room_101.id)
        self.assertEqual(res[0]['occupancy_rate'], 0.0)
        self.assertEqual(res[0]['underutilized'], True)
        
        # 25% (1 bed occupied)
        self._create_allocation(self.b101_bed1, self.analysis_start, self.analysis_end, student_index=1)
        res = AnalyticsService.get_room_utilization(self.analysis_start, self.analysis_end, room_id=self.b_room_101.id)
        self.assertEqual(res[0]['occupancy_rate'], 0.25)
        self.assertEqual(res[0]['underutilized'], True)
        
        # 50% (2 beds occupied) - Threshold is exactly 0.50
        self._create_allocation(self.b101_bed2, self.analysis_start, self.analysis_end, student_index=2)
        res = AnalyticsService.get_room_utilization(self.analysis_start, self.analysis_end, room_id=self.b_room_101.id)
        self.assertEqual(res[0]['occupancy_rate'], 0.50)
        self.assertEqual(res[0]['underutilized'], False) # Exactly threshold -> False
        
        # 75% (3 beds occupied)
        self._create_allocation(self.b101_bed3, self.analysis_start, self.analysis_end, student_index=3)
        res = AnalyticsService.get_room_utilization(self.analysis_start, self.analysis_end, room_id=self.b_room_101.id)
        self.assertEqual(res[0]['occupancy_rate'], 0.75)
        self.assertEqual(res[0]['underutilized'], False)

        # 100%
        self._create_allocation(self.b101_bed4, self.analysis_start, self.analysis_end, student_index=4)
        res = AnalyticsService.get_room_utilization(self.analysis_start, self.analysis_end, room_id=self.b_room_101.id)
        self.assertEqual(res[0]['occupancy_rate'], 1.0)
        self.assertEqual(res[0]['underutilized'], False)

    def test_single_bed_room(self):
        # Room 102 has 1 bed.
        res = AnalyticsService.get_room_utilization(self.analysis_start, self.analysis_end, room_id=self.b_room_102.id)
        self.assertEqual(res[0]['underutilized'], True) # 0.0
        
        self._create_allocation(self.b102_bed1, self.analysis_start, self.analysis_end, student_index=5)
        res = AnalyticsService.get_room_utilization(self.analysis_start, self.analysis_end, room_id=self.b_room_102.id)
        self.assertEqual(res[0]['underutilized'], False) # 1.0

    def test_draft_allocations_ignored(self):
        # Draft (is_active=False)
        self._create_allocation(self.b101_bed1, self.analysis_start, self.analysis_end, is_active=False, student_index=6)
        res = AnalyticsService.get_room_utilization(self.analysis_start, self.analysis_end, room_id=self.b_room_101.id)
        self.assertEqual(res[0]['occupied_beds'], 0) # Ignored

    def test_multiple_allocations_distinct_count(self):
        # Create two overlapping active allocations for the same bed (e.g. data anomaly or overlapping periods)
        # It should still only count the bed as occupied ONCE.
        self._create_allocation(self.b101_bed1, self.analysis_start, self.analysis_end, student_index=7)
        self._create_allocation(self.b101_bed1, self.analysis_start, date(2026, 12, 31), student_index=8, skip_clean=True)
        
        res = AnalyticsService.get_room_utilization(self.analysis_start, self.analysis_end, room_id=self.b_room_101.id)
        self.assertEqual(res[0]['occupied_beds'], 1)
        self.assertEqual(res[0]['total_beds'], 4)

    def test_date_overlap_scenarios(self):
        # We test all 8 scenarios on different beds in the girls hostel (2 beds)
        # 1. Completely before -> NOT counted
        self._create_allocation(self.g201_bed1, date(2025, 1, 1), date(2025, 12, 31), student_index=11)
        res = AnalyticsService.get_room_utilization(self.analysis_start, self.analysis_end, room_id=self.g_room_201.id)
        self.assertEqual(res[0]['occupied_beds'], 0)
        
        # 2. Completely after -> NOT counted
        BedAllocation.objects.all().delete()
        self._create_allocation(self.g201_bed1, date(2028, 1, 1), date(2028, 12, 31), student_index=12)
        res = AnalyticsService.get_room_utilization(self.analysis_start, self.analysis_end, room_id=self.g_room_201.id)
        self.assertEqual(res[0]['occupied_beds'], 0)
        
        # 3. Fully inside -> Counted
        BedAllocation.objects.all().delete()
        self._create_allocation(self.g201_bed1, date(2026, 10, 1), date(2026, 11, 1), student_index=13)
        res = AnalyticsService.get_room_utilization(self.analysis_start, self.analysis_end, room_id=self.g_room_201.id)
        self.assertEqual(res[0]['occupied_beds'], 1)
        
        # 4. Spans entire period -> Counted
        BedAllocation.objects.all().delete()
        self._create_allocation(self.g201_bed1, date(2025, 1, 1), date(2028, 12, 31), student_index=14)
        res = AnalyticsService.get_room_utilization(self.analysis_start, self.analysis_end, room_id=self.g_room_201.id)
        self.assertEqual(res[0]['occupied_beds'], 1)
        
        # 5. Starts before, ends inside -> Counted
        BedAllocation.objects.all().delete()
        self._create_allocation(self.g201_bed1, date(2025, 1, 1), date(2026, 12, 31), student_index=15)
        res = AnalyticsService.get_room_utilization(self.analysis_start, self.analysis_end, room_id=self.g_room_201.id)
        self.assertEqual(res[0]['occupied_beds'], 1)
        
        # 6. Starts inside, ends after -> Counted
        BedAllocation.objects.all().delete()
        self._create_allocation(self.g201_bed1, date(2027, 1, 1), date(2028, 12, 31), student_index=16)
        res = AnalyticsService.get_room_utilization(self.analysis_start, self.analysis_end, room_id=self.g_room_201.id)
        self.assertEqual(res[0]['occupied_beds'], 1)
        
        # 7. Exact boundary start match -> Counted
        BedAllocation.objects.all().delete()
        self._create_allocation(self.g201_bed1, date(2025, 1, 1), self.analysis_start, student_index=17)
        res = AnalyticsService.get_room_utilization(self.analysis_start, self.analysis_end, room_id=self.g_room_201.id)
        self.assertEqual(res[0]['occupied_beds'], 1)
        
        # 8. Exact boundary end match -> Counted
        BedAllocation.objects.all().delete()
        self._create_allocation(self.g201_bed1, self.analysis_end, date(2028, 1, 1), student_index=18)
        res = AnalyticsService.get_room_utilization(self.analysis_start, self.analysis_end, room_id=self.g_room_201.id)
        self.assertEqual(res[0]['occupied_beds'], 1)

    def test_hostel_aggregation(self):
        # Boys hostel has 5 total beds (4 in 101, 1 in 102).
        # We occupy 2 beds in 101, 0 in 102.
        self._create_allocation(self.b101_bed1, self.analysis_start, self.analysis_end, student_index=19)
        self._create_allocation(self.b101_bed2, self.analysis_start, self.analysis_end, student_index=20)
        
        res = AnalyticsService.get_hostel_utilization(self.analysis_start, self.analysis_end)
        
        # Find Boys Hostel in result
        boys_res = next(r for r in res if r['hostel_id'] == self.boys_hostel.id)
        
        self.assertEqual(boys_res['total_beds'], 5)
        self.assertEqual(boys_res['total_rooms'], 2) # Rooms with beds
        self.assertEqual(boys_res['occupied_beds'], 2)
        
        # Utilization = 2/5 = 0.40
        self.assertEqual(boys_res['utilization_rate'], 0.40)
        self.assertEqual(boys_res['underutilized'], True) # < 0.50

        # Now test exactly 49%, 50%, 51% logic if we had 100 beds, but with 5 beds:
        # 2/5 = 40% (True)
        # 3/5 = 60% (False)
        self._create_allocation(self.b101_bed3, self.analysis_start, self.analysis_end, student_index=21)
        res2 = AnalyticsService.get_hostel_utilization(self.analysis_start, self.analysis_end)
        boys_res2 = next(r for r in res2 if r['hostel_id'] == self.boys_hostel.id)
        self.assertEqual(boys_res2['utilization_rate'], 0.60)
        self.assertEqual(boys_res2['underutilized'], False)
