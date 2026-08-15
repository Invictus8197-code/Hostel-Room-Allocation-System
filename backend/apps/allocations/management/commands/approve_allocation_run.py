from django.core.management.base import BaseCommand, CommandError
from backend.apps.allocations.services.allocation_service import AllocationService, InvalidRunStateError
from backend.apps.allocations.models import AllocationRun

class Command(BaseCommand):
    help = 'Approves a DRAFT AllocationRun to prepare it for commit.'

    def add_arguments(self, parser):
        parser.add_argument('--run', type=int, required=True, help='ID of the AllocationRun to approve')

    def handle(self, *args, **options):
        run_id = options['run']
        
        try:
            run = AllocationService.approve_run(run_id=run_id)
            self.stdout.write(self.style.SUCCESS(f'Successfully APPROVED AllocationRun (ID: {run.id}).'))
        except InvalidRunStateError as e:
            raise CommandError(str(e))
        except Exception as e:
            raise CommandError(f'Failed to approve run: {str(e)}')
