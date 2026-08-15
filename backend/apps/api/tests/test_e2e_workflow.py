
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.core.management import call_command
from backend.apps.accounts.models import User
from backend.apps.allocations.models import AllocationRun, BedAllocation
from backend.apps.applications.models import ApplicationBatch
from backend.apps.hostels.models import Bed

class Phase8E2EWorkflowTest(APITestCase):
    
    @classmethod
    def setUpTestData(cls):
        # 1. Run our idempotent seed mechanism
        call_command('seed_data')
        
    def setUp(self):
        # Authenticate as admin
        self.admin = User.objects.get(username='admin')
        self.client.force_authenticate(user=self.admin)
        
        # Get the Demo Batch
        self.batch = ApplicationBatch.objects.get(name="DEMO_Fall 2026 Demo")
        self.boys_beds_count = Bed.objects.filter(room__floor__block__hostel__gender_type='BOYS').count()
        self.girls_beds_count = Bed.objects.filter(room__floor__block__hostel__gender_type='GIRLS').count()
        self.total_beds = self.boys_beds_count + self.girls_beds_count
        
        self.eligible_male_students = self.batch.applications.filter(student__gender='MALE').count()
        self.eligible_female_students = self.batch.applications.filter(student__gender='FEMALE').count()
        self.total_students = self.eligible_male_students + self.eligible_female_students
        
    def test_complete_e2e_workflow(self):
        # 2. Run Optimizer (DRAFT state)
        draft_url = reverse('run-draft')
        draft_res = self.client.post(draft_url, {'batch_id': self.batch.id}, format='json')
        self.assertEqual(draft_res.status_code, status.HTTP_201_CREATED)
        
        run_id = draft_res.data['id']
        self.assertEqual(draft_res.data['status'], 'DRAFT')
        
        # Assert MAXIMUM FEASIBLE ALLOCATION (Not hard-coded 50, but min(capacity, students) partitioned by gender)
        expected_male_allocations = min(self.boys_beds_count, self.eligible_male_students)
        expected_female_allocations = min(self.girls_beds_count, self.eligible_female_students)
        total_expected_allocations = expected_male_allocations + expected_female_allocations
        
        self.assertEqual(draft_res.data['summary_data']['totals']['allocated'], total_expected_allocations)
        self.assertEqual(draft_res.data['summary_data']['totals']['unallocated'], self.total_students - total_expected_allocations)
        
        # Verify Gender Constraints
        allocations = BedAllocation.objects.filter(allocation_run_id=run_id)
        males_in_girls = allocations.filter(student__gender='MALE', bed__room__floor__block__hostel__gender_type='GIRLS').count()
        females_in_boys = allocations.filter(student__gender='FEMALE', bed__room__floor__block__hostel__gender_type='BOYS').count()
        self.assertEqual(males_in_girls, 0)
        self.assertEqual(females_in_boys, 0)
        
        # 3. Approve Run
        approve_url = reverse('run-approve', kwargs={'pk': run_id})
        approve_res = self.client.post(approve_url)
        self.assertEqual(approve_res.status_code, status.HTTP_200_OK)
        self.assertEqual(approve_res.data['status'], 'APPROVED')
        
        # 4. Commit Run
        commit_url = reverse('run-commit', kwargs={'pk': run_id})
        commit_res = self.client.post(commit_url)
        self.assertEqual(commit_res.status_code, status.HTTP_200_OK)
        self.assertEqual(commit_res.data['status'], 'COMMITTED')
        
        # 5. Verify Uniqueness (No Student/Bed has multiple active allocations)
        active_allocations = BedAllocation.objects.filter(is_active=True)
        self.assertEqual(active_allocations.count(), total_expected_allocations)
        
        students_allocated = set(active_allocations.values_list('student_id', flat=True))
        self.assertEqual(len(students_allocated), total_expected_allocations)
        
        beds_allocated = set(active_allocations.values_list('bed_id', flat=True))
        self.assertEqual(len(beds_allocated), total_expected_allocations)
        
        # 6. Verify Analytics updates
        analytics_url = reverse('dashboard_summary')
        analytics_res = self.client.get(analytics_url)
        self.assertEqual(analytics_res.status_code, status.HTTP_200_OK)
        self.assertEqual(analytics_res.data['occupied_beds'], total_expected_allocations)
        self.assertEqual(analytics_res.data['vacant_beds'], self.total_beds - total_expected_allocations)
        
        expected_utilization = total_expected_allocations / self.total_beds if self.total_beds > 0 else 0
        self.assertAlmostEqual(analytics_res.data['utilization'], expected_utilization)
        
        # 7. What-If Simulation
        sim_url = reverse('simulations_run')
        # We run a scenario modifying AC preference
        sim_res = self.client.post(sim_url, {
            'batch_id': self.batch.id,
            'scenario': {'all_ac': True}
        }, format='json')
        self.assertEqual(sim_res.status_code, status.HTTP_200_OK)
        self.assertTrue('simulated' in sim_res.data)
        self.assertTrue('allocated' in sim_res.data['simulated'])
        
        # 8. Verify Simulation Mutated Nothing
        active_allocations_after = BedAllocation.objects.filter(is_active=True).count()
        self.assertEqual(active_allocations_after, total_expected_allocations, "Simulation leaked records!")
        
    def test_concurrency_stale_draft(self):
        draft_url = reverse('run-draft')
        draft_res = self.client.post(draft_url, {'batch_id': self.batch.id}, format='json')
        run_id = draft_res.data['id']
        
        # Approve it
        self.client.post(reverse('run-approve', kwargs={'pk': run_id}))
        
        # Simulate underlying state change (Manually activating one of the allocations to fake a conflict)
        alloc = BedAllocation.objects.filter(allocation_run_id=run_id).first()
        alloc.is_active = True
        alloc.save()
        
        # Commit should FAIL with 409 Conflict
        commit_res = self.client.post(reverse('run-commit', kwargs={'pk': run_id}))
        self.assertEqual(commit_res.status_code, status.HTTP_409_CONFLICT)
        
        # Verify transaction rollback (no allocations from this run should be marked active except the one we faked)
        active_count = BedAllocation.objects.filter(allocation_run_id=run_id, is_active=True).count()
        self.assertEqual(active_count, 1) # Only the one we manually tampered with
