from django.core.management.base import BaseCommand
from django.utils import timezone
from traffic_violation_system.models import Violation

class Command(BaseCommand):
    help = 'Update payment_due_date for violations where it is missing'

    def handle(self, *args, **options):
        violations = Violation.objects.filter(payment_due_date__isnull=True)
        count = violations.count()
        
        self.stdout.write(f"Found {count} violations with missing payment due date")
        
        for violation in violations:
            # Set payment due date to 7 days after violation date
            violation.payment_due_date = violation.violation_date.date() + timezone.timedelta(days=7)
            violation.save(update_fields=['payment_due_date'])
            self.stdout.write(f"Updated violation {violation.id}: Set due date to {violation.payment_due_date}")
            
        self.stdout.write(self.style.SUCCESS(f"Successfully updated {count} violations")) 