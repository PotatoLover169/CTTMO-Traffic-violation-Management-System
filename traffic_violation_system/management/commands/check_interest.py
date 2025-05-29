from django.core.management.base import BaseCommand
from django.utils import timezone
from traffic_violation_system.models import Violation

class Command(BaseCommand):
    help = 'Check interest calculations for all violations'

    def handle(self, *args, **options):
        violations = Violation.objects.all()
        count = violations.count()
        
        self.stdout.write(f"Found {count} total violations")
        
        today = timezone.now().date()
        self.stdout.write(f"Today's date: {today}")
        
        for violation in violations:
            self.stdout.write(f"\nViolation {violation.id}:")
            self.stdout.write(f"  Status: {violation.status}")
            self.stdout.write(f"  Fine Amount: ₱{violation.fine_amount}")
            self.stdout.write(f"  Violation Date: {violation.violation_date}")
            self.stdout.write(f"  Payment Due Date: {violation.payment_due_date}")
            
            if violation.payment_due_date:
                days_overdue = (today - violation.payment_due_date).days
                self.stdout.write(f"  Days Overdue: {days_overdue}")
                
                interest = violation.calculate_interest_amount()
                total = violation.fine_amount + interest
                
                self.stdout.write(f"  Interest Amount: ₱{interest}")
                self.stdout.write(f"  Total with Interest: ₱{total}")
            else:
                self.stdout.write(f"  No payment due date set") 