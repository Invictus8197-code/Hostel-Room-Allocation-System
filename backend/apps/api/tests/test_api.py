from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date
from backend.apps.accounts.models import User, StudentProfile
from backend.apps.applications.models import ApplicationBatch, StudentApplication, Preference
from backend.apps.allocations.models import AllocationRun
from backend.apps.hostels.models import Hostel, Block, Floor, Room, Bed

class APITests(APITestCase):
    def setUp(self):
        # Users
        self.admin = User.objects.create_user(username='admin', role=User.Role.ADMIN, password='password')
        self.warden = User.objects.create_user(username='warden', role=User.Role.WARDEN, password='password')
        self.student = User.objects.create_user(username='student', role=User.Role.STUDENT, password='password')
        
        # Batch
        self.batch = ApplicationBatch.objects.create(name='Fall', start_date=date(2026,9,1), end_date=date(2027,5,31))
        
        # Hostel Setup
        self.hostel = Hostel.objects.create(name="Boys", gender_type=Hostel.GenderType.BOYS)
        b = Block.objects.create(hostel=self.hostel, name="A")
        f = Floor.objects.create(block=b, floor_number=1)
        self.room = Room.objects.create(floor=f, room_number="101", room_type=Room.RoomType.SINGLE, is_ac=False)
        self.bed = Bed.objects.create(room=self.room, bed_number="1")
        
        # Student App
        sp = StudentProfile.objects.create(user=self.student, registration_number='S1', gender=StudentProfile.Gender.MALE, course_year=1, department="CS")
        self.app = StudentApplication.objects.create(batch=self.batch, student=sp, status=StudentApplication.Status.PENDING)

    def _login(self, user):
        resp = self.client.post(reverse('token_obtain_pair'), {'username': user.username, 'password': 'password'})
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + resp.data['access'])
        self.client.cookies['refresh_token'] = resp.cookies['refresh_token']
        return resp

    # Auth Tests
    def test_login_success(self):
        resp = self.client.post(reverse('token_obtain_pair'), {'username': 'admin', 'password': 'password'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)
        self.assertTrue('refresh_token' in resp.cookies)
        self.assertTrue(resp.cookies['refresh_token']['httponly'])

    def test_login_invalid(self):
        resp = self.client.post(reverse('token_obtain_pair'), {'username': 'admin', 'password': 'wrong'})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        resp = self._login(self.admin)
        refresh_resp = self.client.post(reverse('token_refresh'))
        self.assertEqual(refresh_resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_resp.data)

    def test_logout(self):
        self._login(self.admin)
        resp = self.client.post(reverse('logout'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.cookies['refresh_token'].value, '')

    # Permission Tests
    def test_dashboard_admin_access(self):
        self._login(self.admin)
        resp = self.client.get(reverse('dashboard_summary'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_dashboard_warden_access(self):
        self._login(self.warden)
        resp = self.client.get(reverse('dashboard_summary'))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_dashboard_student_denied(self):
        self._login(self.student)
        resp = self.client.get(reverse('dashboard_summary'))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_approve_warden_denied(self):
        run = AllocationRun.objects.create(status=AllocationRun.Status.DRAFT, fairness_score=0, summary_data={})
        self._login(self.warden)
        resp = self.client.post(reverse('run-approve', kwargs={'pk': run.pk}))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    # Allocation Workflow
    def test_draft_approve_commit(self):
        self._login(self.admin)
        
        # 1. Draft
        draft_resp = self.client.post(reverse('run-draft'), {'batch_id': self.batch.id})
        self.assertEqual(draft_resp.status_code, status.HTTP_201_CREATED)
        run_id = draft_resp.data['id']
        
        # 2. Approve
        app_resp = self.client.post(reverse('run-approve', kwargs={'pk': run_id}))
        self.assertEqual(app_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(app_resp.data['status'], AllocationRun.Status.APPROVED)
        
        # 3. Commit
        com_resp = self.client.post(reverse('run-commit', kwargs={'pk': run_id}))
        self.assertEqual(com_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(com_resp.data['status'], AllocationRun.Status.COMMITTED)

    def test_commit_invalid_state(self):
        self._login(self.admin)
        run = AllocationRun.objects.create(status=AllocationRun.Status.DRAFT, fairness_score=0, summary_data={})
        resp = self.client.post(reverse('run-commit', kwargs={'pk': run.pk}))
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)

    # Simulation Safety
    def test_simulation(self):
        self._login(self.admin)
        scenario = {'unavailable_bed_ids': [self.bed.id]}
        resp = self.client.post(reverse('simulations_run'), {'batch_id': self.batch.id, 'scenario': scenario}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['simulated']['allocated'], 0) # Bed was unavailable
        
        # DB remains unchanged
        self.assertEqual(AllocationRun.objects.count(), 0)
