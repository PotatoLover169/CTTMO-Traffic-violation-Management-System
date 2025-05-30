from django.core.management.base import BaseCommand
from traffic_violation_system.models import InterestRateConfiguration

class Command(BaseCommand):
    help = 'Sets up the default interest rate configuration'

    def handle(self, *args, **options):
        config, created = InterestRateConfiguration.objects.get_or_create(
            is_active=True,
            defaults={
                'interest_rate': 1.0,
                'initial_grace_period': 7,
                'monthly_grace_period': 30,
                'notes': 'Default configuration: 1% compound interest after 7 days, compounding monthly (30 days). Interest is calculated on the total amount (fine + previous interest).'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created default interest rate configuration'))
        else:
            self.stdout.write(self.style.SUCCESS('Default interest rate configuration already exists')) 