@login_required
def adjudication_form(request, violation_id):
    # Import the adjudicator permission check
    from .adjudication_views import is_adjudicator
    
    # Check if the user has permission to access this page
    if not is_adjudicator(request.user):
        messages.warning(request, 'You do not have permission to access the adjudication form.')
        # Redirect based on user role
        if hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'ENFORCER':
            return redirect('enforcer_map')
        return redirect('dashboard')
    
    from django.db.models import Q
    
    violation = get_object_or_404(Violation, id=violation_id)
    
    # Get all other violations from the same violator (excluding current one)
    # Now including all statuses, not just PENDING
    previous_violations = Violation.objects.filter(
        violator=violation.violator
    ).exclude(id=violation_id).order_by('-violation_date')
    
    # Also find violations with same license number but different violator records
    if violation.violator and violation.violator.license_number:
        license_violations = Violation.objects.filter(
            violator__license_number=violation.violator.license_number
        ).exclude(
            Q(id=violation_id) | Q(violator=violation.violator)
        ).order_by('-violation_date')
        
        # Combine both querysets
        previous_violations = list(previous_violations) + list(license_violations)
    
    # Also find violations with the same name, even if they're different violator records
    if violation.violator:
        name_violations = Violation.objects.filter(
            Q(violator__first_name__iexact=violation.violator.first_name) &
            Q(violator__last_name__iexact=violation.violator.last_name)
        ).exclude(
            Q(id=violation_id) | Q(violator=violation.violator)
        ).exclude(
            id__in=[v.id for v in previous_violations]
        ).order_by('-violation_date')
        
        # Add name-matched violations to the list
        previous_violations = list(previous_violations) + list(name_violations)
        
    # Sort by violation date (most recent first)
    if previous_violations:
        previous_violations.sort(key=lambda v: v.violation_date, reverse=True)
    
    context = {
        'violation': violation,
        'previous_violations': previous_violations
    }
    
    return render(request, 'violations/adjudication_form.html', context) 