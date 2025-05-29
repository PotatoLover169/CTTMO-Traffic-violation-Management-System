from django.core.management.base import BaseCommand
from django.utils import timezone
from traffic_violation_system.models import Violation

class Command(BaseCommand):
    help = 'Set payment_due_date to a date in the past for testing interest calculations'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=14, help='Number of days in the past to set the due date')
        parser.add_argument('--id', type=int, help='Specific violation ID to update (optional)')

    def handle(self, *args, **options):
        days_past = options['days']
        specific_id = options.get('id')
        
        # Set due date to X days in the past
        past_date = timezone.now().date() - timezone.timedelta(days=days_past)
        
        if specific_id:
            try:
                violation = Violation.objects.get(id=specific_id)
                old_date = violation.payment_due_date
                violation.payment_due_date = past_date
                violation.save(update_fields=['payment_due_date'])
                self.stdout.write(f"Updated violation {violation.id}: Changed due date from {old_date} to {past_date}")
            except Violation.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Violation with ID {specific_id} not found"))
        else:
            violations = Violation.objects.filter(status__in=['PENDING', 'ADJUDICATED', 'APPROVED', 'REJECTED'])
            count = violations.count()
            
            self.stdout.write(f"Found {count} unpaid violations to update")
            
            for violation in violations:
                old_date = violation.payment_due_date
                violation.payment_due_date = past_date
                violation.save(update_fields=['payment_due_date'])
                self.stdout.write(f"Updated violation {violation.id}: Changed due date from {old_date} to {past_date}")
                
            self.stdout.write(self.style.SUCCESS(f"Successfully updated {count} violations")) 