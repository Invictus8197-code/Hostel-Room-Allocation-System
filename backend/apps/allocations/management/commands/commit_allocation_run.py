from django.core.management.base import BaseCommand, CommandError
from backend.apps.allocations.services.allocation_service import AllocationCommitService, InvalidRunStateError, ConcurrencyConflictError
from backend.apps.allocations.models import AllocationRun

class Command(BaseCommand):
    help = 'Commits an APPROVED AllocationRun, activating its allocations.'

    def add_arguments(self, parser):
        parser.add_argument('--run', type=int, required=True, help='ID of the AllocationRun to commit')

    def handle(self, *args, **options):
        run_id = options['run']
        
        try:
            run = AllocationCommitService.commit_run(run_id=run_id)
            self.stdout.write(self.style.SUCCESS(f'Successfully COMMITTED AllocationRun (ID: {run.id}). Beds are now active.'))
        except InvalidRunStateError as e:
            raise CommandError(str(e))
        except ConcurrencyConflictError as e:
            raise CommandError(str(e))
        except Exception as e:
            raise CommandError(f'Failed to commit run: {str(e)}')
