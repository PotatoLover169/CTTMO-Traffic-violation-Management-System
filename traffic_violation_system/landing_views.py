from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from traffic_violation_system.user_portal.models import UserReport, ReportAttachment

def landing_home(request):
    """View for the landing page."""
    return render(request, 'landing/home.html')


def about(request):
    """View for the about page."""
    return render(request, 'landing/about.html')


def services(request):
    """View for the services page."""
    return render(request, 'landing/services.html')


def contact(request):
    """View for the contact page."""
    return render(request, 'landing/contact.html')


def public_report(request):
    """View for anonymous users to submit reports without an account."""
    if request.method == 'POST':
        report_type = request.POST.get('type')
        subject = request.POST.get('subject')
        description = request.POST.get('description')
        location = request.POST.get('location')
        phone_number = request.POST.get('phone_number')
        incident_date = request.POST.get('incident_date')
        reporter_name = request.POST.get('name')
        reporter_email = request.POST.get('email')
        attachment = request.FILES.get('attachment')  # Keep for backward compatibility
        
        # Create the report with public user info
        report = UserReport.objects.create(
            type=report_type,
            subject=subject,
            description=description,
            location=location,
            phone_number=phone_number,
            incident_date=incident_date,
            attachment=attachment,  # Keep for backward compatibility
            reporter_name=reporter_name,
            reporter_email=reporter_email,
            is_anonymous=True
        )
        
        # Handle multiple attachments if present
        if 'attachments' in request.FILES:
            files = request.FILES.getlist('attachments')
            
            # Limit to max 5 attachments
            for file in files[:5]:
                # Check file size (5MB limit)
                if file.size <= 5 * 1024 * 1024:
                    ReportAttachment.objects.create(
                        report=report,
                        file=file
                    )
        
        # Add success message
        messages.success(request, 'Your report has been submitted successfully. Thank you for helping keep our roads safe!')
        
        # Redirect to landing page
        return redirect('landing_home')
    
    context = {
        'report_types': UserReport.REPORT_TYPES,
    }
    
    return render(request, 'landing/public_report.html', context) 