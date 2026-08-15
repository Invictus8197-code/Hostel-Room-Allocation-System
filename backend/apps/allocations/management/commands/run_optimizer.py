from django.core.management.base import BaseCommand, CommandError
from backend.apps.allocations.services.allocation_service import AllocationService, OptimizationError, InvalidBatchError
from backend.apps.applications.models import ApplicationBatch
import json

class Command(BaseCommand):
    help = 'Runs the Google OR-Tools CP-SAT optimizer for a given ApplicationBatch to create a DRAFT allocation'

    def add_arguments(self, parser):
        parser.add_argument('--batch', type=int, required=True, help='ID of the ApplicationBatch to optimize')

    def handle(self, *args, **options):
        batch_id = options['batch']
        
        try:
            batch = ApplicationBatch.objects.get(id=batch_id)
        except ApplicationBatch.DoesNotExist:
            raise CommandError(f'ApplicationBatch with ID {batch_id} does not exist.')
            
        self.stdout.write(self.style.SUCCESS(f'Starting optimizer for Batch: {batch.name} (ID: {batch.id})'))
        
        try:
            run = AllocationService.create_draft_run(batch_id=batch_id)
        except InvalidBatchError as e:
            raise CommandError(str(e))
        except OptimizationError as e:
            raise CommandError(str(e))
        except Exception as e:
            raise CommandError(f'Optimizer failed with unexpected error: {str(e)}')
            
        self.stdout.write(self.style.SUCCESS(f'Successfully created DRAFT AllocationRun (ID: {run.id}).'))
        self.stdout.write("Summary Data:")
        self.stdout.write(json.dumps(run.summary_data, indent=2))
