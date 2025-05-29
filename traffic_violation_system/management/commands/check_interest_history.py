from django.core.management.base import BaseCommand
from traffic_violation_system.models import ViolationInterestHistory

class Command(BaseCommand):
    help = 'Check interest history records'

    def handle(self, *args, **options):
        history_records = ViolationInterestHistory.objects.all()
        count = history_records.count()
        
        self.stdout.write(f"Found {count} interest history records")
        
        for history in history_records:
            self.stdout.write(f"\nInterest History ID: {history.id}")
            self.stdout.write(f"  Violation ID: {history.violation.id}")
            self.stdout.write(f"  Interest Amount: ₱{history.interest_amount}")
            self.stdout.write(f"  Calculation Date: {history.calculation_date}")
            self.stdout.write(f"  Months Overdue: {history.months_overdue}")
            self.stdout.write(f"  Interest Rate: {history.interest_rate_used}%")
            if history.calculated_by:
                self.stdout.write(f"  Calculated By: {history.calculated_by.username}")
            else:
                self.stdout.write(f"  Calculated By: System") 