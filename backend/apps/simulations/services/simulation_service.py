from django.db.models import Exists, OuterRef, Count
from backend.apps.applications.models import ApplicationBatch, StudentApplication
from backend.apps.allocations.models import BedAllocation
from backend.apps.hostels.models import Bed
from backend.apps.allocations.services.optimizer import HostelOptimizer
from backend.apps.analytics.services import AnalyticsService

class SimulationService:
    
    @staticmethod
    def run_simulation(batch_id: int, scenario: dict = None) -> dict:
        scenario = scenario or {}
        
        # 1. Validate batch
        try:
            batch = ApplicationBatch.objects.get(id=batch_id)
        except ApplicationBatch.DoesNotExist:
            raise ValueError(f"Batch {batch_id} not found.")
            
        # 2. Validate subset
        student_ids = scenario.get('student_ids')
        if student_ids is not None:
            # Check if all student IDs actually belong to this batch
            valid_students = StudentApplication.objects.filter(batch=batch, student_id__in=student_ids)
            if valid_students.count() != len(student_ids):
                raise ValueError("One or more student IDs in the scenario do not belong to the requested batch.")
                
        # 3. Baseline Population & Current Metrics
        if student_ids is not None:
            population_qs = StudentApplication.objects.filter(batch=batch, student_id__in=student_ids)
        else:
            population_qs = StudentApplication.objects.filter(batch=batch)
            
        population_student_ids = list(population_qs.values_list('student_id', flat=True))
        
        current_active_allocations = BedAllocation.objects.filter(
            is_active=True,
            start_date__lt=batch.end_date,
            end_date__gt=batch.start_date
        )
        
        # Current allocated for the population
        current_allocated = current_active_allocations.filter(student_id__in=population_student_ids).count()
        current_unallocated = len(population_student_ids) - current_allocated
        
        # Current global metrics (using Phase 5 Analytics Service)
        hostel_utils = AnalyticsService.get_hostel_utilization(batch.start_date, batch.end_date)
        total_beds = sum(h['total_beds'] for h in hostel_utils)
        current_occupied_beds = sum(h['occupied_beds'] for h in hostel_utils)
        
        current_occupancy_rate = current_occupied_beds / total_beds if total_beds > 0 else 0.0
        
        # Calculate current fairness for the population if we wanted, but we'll leave it as 0.0 if not optimized
        # Or if we want to be exact, we just output 0.0 for current fairness since it hasn't been scored by the optimizer.
        current_fairness_score = 0.0
        
        # 4. Run Optimizer with Scenario
        optimizer = HostelOptimizer(batch_id, scenario=scenario)
        opt_result = optimizer.run()
        
        # 5. Simulated Metrics
        # The optimizer assignments are hypothetical. We overlay them on top of existing active allocations.
        # However, we must EXCLUDE existing active allocations belonging to the population, 
        # because the simulation is replacing their state. Wait, the optimizer automatically EXCLUDES 
        # students who already have active allocations in this batch! 
        # "select_eligible_students() Exclude students with active/overlapping allocations"
        # So the optimizer only assigns beds to students who are currently UNALLOCATED.
        # Therefore, simulated occupied beds = (Current active beds) UNION (Newly assigned beds).
        
        # We need the set of bed IDs that are currently occupied
        occupied_bed_ids = set(current_active_allocations.values_list('bed_id', flat=True))
        
        # Add the new assignments
        assigned_bed_ids = set()
        student_bed_assignments = []
        for app, bed in opt_result.get('assignments', []):
            assigned_bed_ids.add(bed.id)
            student_bed_assignments.append({
                "student_id": app.student.id,
                "bed_id": bed.id
            })
            
        simulated_occupied_beds_set = occupied_bed_ids.union(assigned_bed_ids)
        simulated_occupied_beds = len(simulated_occupied_beds_set)
        
        simulated_occupancy_rate = simulated_occupied_beds / total_beds if total_beds > 0 else 0.0
        
        # Population allocated in simulation: 
        # = (Already allocated in population) + (Newly allocated by optimizer)
        simulated_allocated = current_allocated + opt_result.get('allocated_count', 0)
        simulated_unallocated = len(population_student_ids) - simulated_allocated
        
        simulated_fairness_score = opt_result.get('fairness_score', 0.0)

        # 6. Build the Result Object
        return {
            "scenario": scenario,
            "current": {
                "allocated": current_allocated,
                "unallocated": current_unallocated,
                "occupancy_rate": current_occupancy_rate,
                "vacancy_rate": 1.0 - current_occupancy_rate if total_beds > 0 else 0.0,
                "utilization_rate": current_occupancy_rate,
                "fairness_score": current_fairness_score
            },
            "simulated": {
                "allocated": simulated_allocated,
                "unallocated": simulated_unallocated,
                "occupancy_rate": simulated_occupancy_rate,
                "vacancy_rate": 1.0 - simulated_occupancy_rate if total_beds > 0 else 0.0,
                "utilization_rate": simulated_occupancy_rate,
                "fairness_score": simulated_fairness_score
            },
            "difference": {
                "allocated": simulated_allocated - current_allocated,
                "unallocated": simulated_unallocated - current_unallocated,
                "occupancy_rate": simulated_occupancy_rate - current_occupancy_rate,
                "vacancy_rate": (1.0 - simulated_occupancy_rate) - (1.0 - current_occupancy_rate) if total_beds > 0 else 0.0,
                "utilization_rate": simulated_occupancy_rate - current_occupancy_rate,
                "fairness_score": simulated_fairness_score - current_fairness_score
            },
            "allocation": {
                "student_bed_assignments": student_bed_assignments
            },
            "summary": {
                "message": "Simulation successful",
                "status": opt_result.get('status')
            }
        }
