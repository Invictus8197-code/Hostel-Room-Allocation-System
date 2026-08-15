from django.db import transaction
from backend.apps.applications.models import ApplicationBatch, StudentApplication
from backend.apps.allocations.models import BedAllocation, AllocationRun
from backend.apps.hostels.models import Bed
from backend.apps.allocations.services.optimizer import HostelOptimizer

class InvalidBatchError(Exception):
    pass

class InvalidRunStateError(Exception):
    pass

class ConcurrencyConflictError(Exception):
    pass

class OptimizationError(Exception):
    pass

class AllocationService:
    @classmethod
    def create_draft_run(cls, batch_id):
        try:
            batch = ApplicationBatch.objects.get(id=batch_id)
        except ApplicationBatch.DoesNotExist:
            raise InvalidBatchError(f"Batch {batch_id} not found.")

        # Run Optimizer
        optimizer = HostelOptimizer(batch_id)
        try:
            result = optimizer.run()
        except Exception as e:
            raise OptimizationError(f"Optimizer failed: {str(e)}")

        status = result.get('status')
        # Only valid statuses or empty results
        if status not in ['OPTIMAL', 'FEASIBLE', 'INFEASIBLE']:
            raise OptimizationError(f"Optimizer returned failure status: {status}")

        summary_data = {
            "totals": {
                "eligible_students": result['eligible_students'],
                "available_beds": result['available_beds'],
                "allocated": result['allocated_count'],
                "unallocated": result['unallocated_count']
            },
            "preference_score": {
                "total": result['total_preference_points'],
                "maximum": result['eligible_students'] * 15 # Theoretical maximum
            },
            "fairness": {
                "score": result['fairness_score']
            },
            "unallocated_reasons": {
                "no_compatible_gender_beds": result['unallocated_count'] # Simplified reason mapping
            }
        }

        with transaction.atomic():
            run = AllocationRun.objects.create(
                status=AllocationRun.Status.DRAFT,
                fairness_score=result['fairness_score'],
                summary_data=summary_data
            )

            allocations_to_create = []
            for app, bed in result['assignments']:
                allocations_to_create.append(BedAllocation(
                    student=app.student,
                    bed=bed,
                    allocation_run=run,
                    start_date=batch.start_date,
                    end_date=batch.end_date,
                    is_active=False # MUST BE FALSE FOR DRAFT
                ))

            BedAllocation.objects.bulk_create(allocations_to_create)

        return run

    @classmethod
    def approve_run(cls, run_id):
        with transaction.atomic():
            try:
                run = AllocationRun.objects.select_for_update().get(id=run_id)
            except AllocationRun.DoesNotExist:
                raise InvalidRunStateError("Run does not exist.")

            if run.status != AllocationRun.Status.DRAFT:
                raise InvalidRunStateError(f"Cannot approve run in {run.status} state.")

            run.status = AllocationRun.Status.APPROVED
            run.save(update_fields=['status'])

        return run


class AllocationCommitService:
    @classmethod
    def commit_run(cls, run_id):
        with transaction.atomic():
            try:
                run = AllocationRun.objects.select_for_update().get(id=run_id)
            except AllocationRun.DoesNotExist:
                raise InvalidRunStateError("Run does not exist.")

            if run.status != AllocationRun.Status.APPROVED:
                raise InvalidRunStateError(f"Only APPROVED runs can be committed. Current status: {run.status}")

            draft_allocations = list(run.bed_allocations.select_for_update().all())
            
            if not draft_allocations:
                # Valid empty run
                run.status = AllocationRun.Status.COMMITTED
                run.save(update_fields=['status'])
                return run

            # Use batch dates from the draft allocations
            start_date = draft_allocations[0].start_date
            end_date = draft_allocations[0].end_date

            bed_ids = [alloc.bed_id for alloc in draft_allocations]
            student_ids = [alloc.student_id for alloc in draft_allocations]

            # Lock the target beds
            list(Bed.objects.select_for_update().filter(id__in=bed_ids))
            
            # Lock the target student applications
            list(StudentApplication.objects.select_for_update().filter(student_id__in=student_ids, batch__start_date=start_date, batch__end_date=end_date))

            # Re-check bed availability
            overlapping_beds = BedAllocation.objects.filter(
                bed_id__in=bed_ids,
                is_active=True,
                start_date__lt=end_date,
                end_date__gt=start_date
            ).exists()

            if overlapping_beds:
                raise ConcurrencyConflictError("Concurrency conflict: One or more selected beds were allocated by another process.")

            # Re-check student availability
            overlapping_students = BedAllocation.objects.filter(
                student_id__in=student_ids,
                is_active=True,
                start_date__lt=end_date,
                end_date__gt=start_date
            ).exists()

            if overlapping_students:
                raise ConcurrencyConflictError("Concurrency conflict: One or more selected students were allocated by another process.")

            # Update allocations to active
            for alloc in draft_allocations:
                alloc.is_active = True
                
            BedAllocation.objects.bulk_update(draft_allocations, ['is_active'])

            # Update StudentApplication status
            applications = StudentApplication.objects.filter(
                student_id__in=student_ids, 
                batch__start_date=start_date, 
                batch__end_date=end_date
            )
            applications.update(status=StudentApplication.Status.ALLOCATED)

            # Mark run as COMMITTED
            run.status = AllocationRun.Status.COMMITTED
            run.save(update_fields=['status'])

        return run
