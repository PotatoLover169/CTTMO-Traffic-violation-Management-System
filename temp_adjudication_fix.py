from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Violation
from .adjudication_views import is_adjudicator

@login_required
def adjudication_list(request):
    # Check if the user has permission to access this page
    if not is_adjudicator(request.user):
        messages.warning(request, 'You do not have permission to access the adjudication list.')
        # Redirect based on user role
        if hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'ENFORCER':
            return redirect('enforcer_map')
        return redirect('dashboard')
    
    # Get all violations without PAID status
    violations = Violation.objects.select_related('violator', 'enforcer').exclude(status='PAID').order_by('-violation_date')
    
    # Enhanced search functionality
    search_query = request.GET.get('search', '').strip()
    if search_query:
        violations = violations.filter(
            Q(violator__first_name__icontains=search_query) |
            Q(violator__last_name__icontains=search_query) |
            Q(violator__license_number__icontains=search_query) |
            Q(violation_type__icontains=search_query) |
            Q(vehicle_type__icontains=search_query) |
            Q(plate_number__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(status__icontains=search_query)
        ).distinct()

    # Pagination - 15 items per page
    paginator = Paginator(violations, 15)
    page = request.GET.get('page', 1)
    try:
        violations = paginator.page(page)
    except PageNotAnInteger:
        violations = paginator.page(1)
    except EmptyPage:
        violations = paginator.page(paginator.num_pages)

    context = {
        'violations': violations,
        'page_obj': violations,
        'search_query': search_query,
        'total_count': paginator.count
    }
    return render(request, 'violations/adjudication_list.html', context) 