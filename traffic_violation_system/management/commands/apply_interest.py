from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from traffic_violation_system.models import Violation

class Command(BaseCommand):
    help = 'Apply interest to all unpaid violations'

    def handle(self, *args, **options):
        # Get all unpaid violations that are past due
        unpaid_violations = Violation.objects.filter(
            status__in=['PENDING', 'ADJUDICATED', 'APPROVED', 'REJECTED'],
            payment_due_date__lt=timezone.now().date()
        )
        
        self.stdout.write(f"Found {unpaid_violations.count()} unpaid violations past due date")
        
        # Get a staff user for the record
        admin_user = User.objects.filter(is_staff=True).first()
        if not admin_user:
            self.stdout.write(self.style.ERROR("No staff user found to attribute interest calculations to"))
            return
            
        violations_processed = 0
        total_interest = 0
        
        # Print details about each violation
        for violation in Violation.objects.all():
            self.stdout.write(f"\nViolation {violation.id}:")
            self.stdout.write(f"  Status: {violation.status}")
            self.stdout.write(f"  Due Date: {violation.payment_due_date}")
            self.stdout.write(f"  Today: {timezone.now().date()}")
            
            if not violation.payment_due_date:
                self.stdout.write(f"  Skipping - No payment due date set")
            elif violation.status == 'PAID':
                self.stdout.write(f"  Skipping - Already paid")
            elif violation.payment_due_date >= timezone.now().date():
                self.stdout.write(f"  Skipping - Not past due date")
            else:
                days_overdue = (timezone.now().date() - violation.payment_due_date).days
                self.stdout.write(f"  Days overdue: {days_overdue}")
                
                # Calculate and record interest
                interest = violation.record_interest_calculation(user=admin_user)
                if interest:
                    violations_processed += 1
                    total_interest += interest
                    self.stdout.write(f"  Interest applied: ₱{interest}")
                else:
                    self.stdout.write(f"  No interest applied (may be within grace period)")
        
        self.stdout.write(self.style.SUCCESS(f"Applied interest to {violations_processed} violations. Total interest: ₱{total_interest}")) 