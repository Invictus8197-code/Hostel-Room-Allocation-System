from ortools.sat.python import cp_model
from django.db import transaction
from backend.apps.applications.models import StudentApplication, ApplicationBatch, Preference
from backend.apps.allocations.models import BedAllocation, AllocationRun
from backend.apps.hostels.models import Bed, Hostel
from backend.apps.accounts.models import StudentProfile

class HostelOptimizer:
    def __init__(self, batch_id, scenario=None):
        self.batch_id = batch_id
        self.scenario = scenario or {}
        self.batch = None
        self.eligible_students = []
        self.available_beds = []
        
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        self.X = {} # decision variables
        self.preferences = {} # preference mapping
        
        self.status = None
        self.allocated_count = 0
        self.total_preference_points = 0
        self.fairness_score = 0.0
        self.assignments = []

    def validate_batch(self):
        try:
            self.batch = ApplicationBatch.objects.get(id=self.batch_id)
        except ApplicationBatch.DoesNotExist:
            raise ValueError(f"Batch {self.batch_id} not found.")

    def select_eligible_students(self):
        # Exclude students with active/overlapping allocations for this batch period
        # existing_start < requested_end AND existing_end > requested_start
        overlapping_allocations = BedAllocation.objects.filter(
            is_active=True,
            start_date__lt=self.batch.end_date,
            end_date__gt=self.batch.start_date
        ).values_list('student_id', flat=True)
        
        qs = StudentApplication.objects.filter(
            batch=self.batch,
            status=StudentApplication.Status.PENDING
        ).exclude(student_id__in=overlapping_allocations).select_related('student', 'preference')
        
        student_ids = self.scenario.get('student_ids')
        if student_ids is not None:
            qs = qs.filter(student_id__in=student_ids)
            
        self.eligible_students = list(qs)

    def select_available_beds(self):
        # Exclude beds with active/overlapping allocations for this batch period
        overlapping_beds = BedAllocation.objects.filter(
            is_active=True,
            start_date__lt=self.batch.end_date,
            end_date__gt=self.batch.start_date
        ).values_list('bed_id', flat=True)
        
        qs = Bed.objects.exclude(
            id__in=overlapping_beds
        ).select_related('room', 'room__floor__block__hostel')
        
        unavailable_bed_ids = self.scenario.get('unavailable_bed_ids')
        if unavailable_bed_ids:
            qs = qs.exclude(id__in=unavailable_bed_ids)
            
        self.available_beds = list(qs)

    def _is_gender_compatible(self, student_gender, hostel_gender):
        if student_gender == StudentProfile.Gender.MALE and hostel_gender == Hostel.GenderType.BOYS:
            return True
        if student_gender == StudentProfile.Gender.FEMALE and hostel_gender == Hostel.GenderType.GIRLS:
            return True
        # OTHER gender or unsupported hostel types are not compatible
        return False

    def build_model(self):
        # Create decision variables only for valid combinations
        for app in self.eligible_students:
            for bed in self.available_beds:
                if self._is_gender_compatible(app.student.gender, bed.room.floor.block.hostel.gender_type):
                    self.X[app.id, bed.id] = self.model.NewBoolVar(f'x_{app.id}_{bed.id}')
        
        # Hard constraint: One student per bed
        for bed in self.available_beds:
            variables_for_bed = [self.X[app.id, bed.id] for app in self.eligible_students if (app.id, bed.id) in self.X]
            if variables_for_bed:
                self.model.AddAtMostOne(variables_for_bed)
            
        # Hard constraint: One bed per student
        for app in self.eligible_students:
            variables_for_student = [self.X[app.id, bed.id] for bed in self.available_beds if (app.id, bed.id) in self.X]
            if variables_for_student:
                self.model.AddAtMostOne(variables_for_student)
            
        # Objective function
        objective_terms = []
        preference_overrides = self.scenario.get('preference_overrides', {})
        
        for app in self.eligible_students:
            # Immutable dictionary preference fallback
            override = preference_overrides.get(app.student.id, {})
            
            try:
                pref = app.preference
                pref_room_type = override.get('preferred_room_type', pref.preferred_room_type)
                pref_ac = override.get('preferred_ac', pref.preferred_ac)
            except Preference.DoesNotExist:
                pref = None
                pref_room_type = override.get('preferred_room_type')
                pref_ac = override.get('preferred_ac')

            for bed in self.available_beds:
                if (app.id, bed.id) in self.X:
                    score = 0
                    if pref or override:
                        if pref_room_type is not None and pref_room_type == bed.room.room_type:
                            score += 10
                        if pref_ac is not None and pref_ac == bed.room.is_ac:
                            score += 5
                            
                    self.preferences[(app.id, bed.id)] = score
                    
                    # Weight allocation count by 1000 to prioritize it over preferences
                    objective_terms.append(self.X[app.id, bed.id] * (1000 + score))
                    
        self.model.Maximize(sum(objective_terms))

    def solve(self):
        self.status = self.solver.Solve(self.model)
        
        if self.status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            max_possible_pref = 0
            for app in self.eligible_students:
                for bed in self.available_beds:
                    if (app.id, bed.id) in self.X and self.solver.Value(self.X[app.id, bed.id]):
                        self.assignments.append((app, bed))
                        self.allocated_count += 1
                        self.total_preference_points += self.preferences[(app.id, bed.id)]
                        max_possible_pref += 15 # Max possible score for one assignment
                        
            if max_possible_pref > 0:
                self.fairness_score = self.total_preference_points / max_possible_pref
            else:
                self.fairness_score = 0.0

    def run(self):
        self.validate_batch()
        self.select_eligible_students()
        self.select_available_beds()
        
        # If no eligible students or beds, we can return early
        if not self.eligible_students or not self.available_beds:
            return {
                'status': 'INFEASIBLE' if not self.available_beds and self.eligible_students else 'OPTIMAL',
                'eligible_students': len(self.eligible_students),
                'available_beds': len(self.available_beds),
                'allocated_count': 0,
                'unallocated_count': len(self.eligible_students),
                'total_preference_points': 0,
                'fairness_score': 0.0,
                'assignments': []
            }
            
        self.build_model()
        self.solve()
        
        status_name = self.solver.StatusName(self.status)
        return {
            'status': status_name,
            'eligible_students': len(self.eligible_students),
            'available_beds': len(self.available_beds),
            'allocated_count': self.allocated_count,
            'unallocated_count': len(self.eligible_students) - self.allocated_count,
            'total_preference_points': self.total_preference_points,
            'fairness_score': self.fairness_score,
            'assignments': self.assignments
        }
