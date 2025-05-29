from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from .models import InterestRateConfiguration, Violation, ViolationInterestHistory
from .forms import InterestRateConfigForm
from traffic_violation_system.views import log_activity

@login_required
@user_passes_test(lambda u: u.is_staff)
def interest_rate_config(request):
    """
    View to manage interest rate configurations
    """
    configs = InterestRateConfiguration.objects.all().order_by('-created_at')
    active_config = InterestRateConfiguration.objects.filter(is_active=True).first()
    
    # Calculate total affected violations
    unpaid_violations = Violation.objects.filter(
        status__in=['PENDING', 'ADJUDICATED', 'APPROVED', 'REJECTED'],
    ).exclude(payment_due_date__gt=timezone.now().date())
    
    # Calculate potential revenue from interest
    total_interest = Decimal('0.00')
    violations_with_interest = 0
    if active_config:
        for violation in unpaid_violations:
            interest = violation.calculate_interest_amount()
            if interest > 0:
                violations_with_interest += 1
                total_interest += interest
    
    if request.method == 'POST':
        form = InterestRateConfigForm(request.POST)
        if form.is_valid():
            config = form.save(commit=False)
            config.created_by = request.user
            config.updated_by = request.user
            
            # Deactivate all other configs if this one is active
            if config.is_active:
                InterestRateConfiguration.objects.filter(is_active=True).update(is_active=False)
                
            config.save()
            
            # Log activity
            log_activity(
                user=request.user,
                action='Created Interest Rate Configuration',
                details=f'Interest Rate: {config.interest_rate}%, Initial Grace: {config.initial_grace_period} days, Monthly Grace: {config.monthly_grace_period} days',
                category='system'
            )
            
            messages.success(request, 'Interest rate configuration created successfully.')
            return redirect('interest_rate_config')
    else:
        form = InterestRateConfigForm()
        
        # If active config exists, pre-fill the form
        if active_config:
            form = InterestRateConfigForm(initial={
                'interest_rate': active_config.interest_rate,
                'initial_grace_period': active_config.initial_grace_period,
                'monthly_grace_period': active_config.monthly_grace_period,
                'notes': ''
            })
    
    context = {
        'configs': configs,
        'active_config': active_config,
        'form': form,
        'unpaid_violations_count': unpaid_violations.count(),
        'violations_with_interest': violations_with_interest,
        'total_interest': total_interest,
    }
    
    return render(request, 'admin/interest_rate_config.html', context)


@login_required
@user_passes_test(lambda u: u.is_staff)
def toggle_interest_config(request, config_id):
    """
    Toggle the active status of a configuration
    """
    config = get_object_or_404(InterestRateConfiguration, id=config_id)
    
    if config.is_active:
        config.is_active = False
        config.save()
        messages.success(request, 'Interest rate configuration deactivated.')
    else:
        # Deactivate all other configs
        InterestRateConfiguration.objects.filter(is_active=True).update(is_active=False)
        
        # Activate this one
        config.is_active = True
        config.updated_by = request.user
        config.save()
        messages.success(request, 'Interest rate configuration activated.')
    
    log_activity(
        user=request.user,
        action=f'{"Activated" if config.is_active else "Deactivated"} Interest Rate Configuration',
        details=f'Configuration ID: {config.id}',
        category='system'
    )
    
    return redirect('interest_rate_config')


@login_required
@user_passes_test(lambda u: u.is_staff)
def apply_interest_to_all(request):
    """
    Apply interest calculations to all unpaid violations and record in history
    """
    if request.method == 'POST':
        # Get all unpaid violations that are past due
        unpaid_violations = Violation.objects.filter(
            status__in=['PENDING', 'ADJUDICATED', 'APPROVED', 'REJECTED'],
            payment_due_date__lt=timezone.now().date()
        )
        
        print(f"DEBUG: Total violations with status in ['PENDING', 'ADJUDICATED', 'APPROVED', 'REJECTED']: {Violation.objects.filter(status__in=['PENDING', 'ADJUDICATED', 'APPROVED', 'REJECTED']).count()}")
        print(f"DEBUG: Found {unpaid_violations.count()} unpaid violations past due date")
        
        # Print details about each violation
        for violation in Violation.objects.all():
            print(f"DEBUG: Violation ID: {violation.id}, Status: {violation.status}, Due Date: {violation.payment_due_date}, Today: {timezone.now().date()}")
            if not violation.payment_due_date:
                print(f"DEBUG: Skipping violation {violation.id} - No payment due date set")
            elif violation.status == 'PAID':
                print(f"DEBUG: Skipping violation {violation.id} - Already paid")
            elif violation.payment_due_date >= timezone.now().date():
                print(f"DEBUG: Skipping violation {violation.id} - Not past due date")
            else:
                days_overdue = (timezone.now().date() - violation.payment_due_date).days
                print(f"DEBUG: Violation {violation.id} - Days overdue: {days_overdue}")
        
        violations_processed = 0
        total_interest = Decimal('0.00')
        
        for violation in unpaid_violations:
            interest = violation.record_interest_calculation(user=request.user)
            if interest:
                violations_processed += 1
                total_interest += interest
        
        # Log activity
        log_activity(
            user=request.user,
            action='Applied Interest to All Violations',
            details=f'Processed {violations_processed} violations, Total interest: ₱{total_interest}',
            category='system'
        )
        
        messages.success(request, f'Applied interest to {violations_processed} violations. Total interest: ₱{total_interest}')
        
    return redirect('interest_rate_config')

@login_required
@user_passes_test(lambda u: u.is_staff)
def violation_interest_history(request, violation_id):
    """
    Show interest history for a specific violation
    """
    violation = get_object_or_404(Violation, id=violation_id)
    interest_history = ViolationInterestHistory.objects.filter(violation=violation).order_by('-calculation_date')
    
    current_interest = violation.calculate_interest_amount()
    total_with_interest = violation.fine_amount + current_interest
    
    context = {
        'violation': violation,
        'interest_history': interest_history,
        'current_interest': current_interest,
        'total_with_interest': total_with_interest,
        'now': timezone.now(),
    }
    
    return render(request, 'admin/violation_interest_history.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def record_violation_interest(request, violation_id):
    """
    Calculate and record interest for a specific violation
    """
    violation = get_object_or_404(Violation, id=violation_id)
    interest = violation.record_interest_calculation(user=request.user)
    
    if interest:
        messages.success(request, f'Interest of ₱{interest} recorded successfully.')
    else:
        messages.info(request, 'No interest to record at this time.')
    
    return redirect('violation_interest_history', violation_id=violation.id)

@login_required
@user_passes_test(lambda u: u.is_staff)
def delete_interest_config(request, config_id):
    """
    Delete an interest rate configuration (only if it's not active)
    """
    config = get_object_or_404(InterestRateConfiguration, id=config_id)
    
    # Don't allow deletion of active configurations
    if config.is_active:
        messages.error(request, "Cannot delete an active interest rate configuration. Deactivate it first.")
        return redirect('interest_rate_config')
    
    # Store details for logging
    details = f'Deleted configuration: Interest Rate: {config.interest_rate}%, Initial Grace: {config.initial_grace_period} days, Monthly Grace: {config.monthly_grace_period} days'
    
    # Delete the configuration
    config.delete()
    
    # Log the activity
    log_activity(
        user=request.user,
        action='Deleted Interest Rate Configuration',
        details=details,
        category='system'
    )
    
    messages.success(request, 'Interest rate configuration deleted successfully.')
    return redirect('interest_rate_config') 