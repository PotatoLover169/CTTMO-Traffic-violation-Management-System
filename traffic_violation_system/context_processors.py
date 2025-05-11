from django.db.models import Q
from traffic_violation_system.user_portal.models import UserNotification
from django.conf import settings
import json

def user_notifications(request):
    """Add unread notification count and recent notifications to the context"""
    context = {
        'unread_notification_count': 0,
        'recent_notifications': [],
    }
    
    if request.user.is_authenticated:
        # Count unread notifications
        context['unread_notification_count'] = UserNotification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        # Get recent notifications for the dropdown menu (increased from 5 to 10)
        context['recent_notifications'] = UserNotification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:10]
    
    return context

def recaptcha_settings(request):
    """Add reCAPTCHA site key to all templates"""
    # Get the current domain from the request
    current_domain = request.get_host().split(':')[0]  # Remove port if present
    
    # Get allowed domains from settings
    allowed_domains = getattr(settings, 'RECAPTCHA_ALLOWED_DOMAINS', [])
    
    # Ensure the current domain is in the allowed list
    if current_domain not in allowed_domains:
        allowed_domains.append(current_domain)
    
    # Convert to JSON format
    allowed_domains_json = json.dumps(allowed_domains)
    
    return {
        'recaptcha_site_key': getattr(settings, 'RECAPTCHA_SITE_KEY', '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI'),  # Using test key as fallback
        'recaptcha_current_domain': current_domain,
        'recaptcha_allowed_domains': allowed_domains_json,
    } 