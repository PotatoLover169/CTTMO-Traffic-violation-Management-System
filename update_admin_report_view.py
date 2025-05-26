import re
import os

def update_admin_report_view():
    # Path to the views.py file
    views_path = os.path.join('traffic_violation_system', 'views.py')
    
    # Make sure the file exists
    if not os.path.exists(views_path):
        print(f"File not found: {views_path}")
        return False
    
    # Read the contents of the file
    with open(views_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match the admin_report_view function
    pattern = r'@user_passes_test\(lambda u: u\.is_staff\)\s*def admin_report_view\(request, report_id\):.*?return render\(request, \'admin/reports/report_detail\.html\', context\)'
    
    # Replacement with attachments included
    replacement = '''@user_passes_test(lambda u: u.is_staff)
def admin_report_view(request, report_id):
    """View a single report in a modal or detailed page."""
    from traffic_violation_system.user_portal.models import ReportAttachment
    
    report = get_object_or_404(UserReport, id=report_id)
    
    # Get report attachments
    attachments = ReportAttachment.objects.filter(report=report).order_by('uploaded_at')
    
    context = {
        'report': report,
        'attachments': attachments,
    }
    
    # If this is an AJAX request, return the modal content
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'admin/reports/report_modal.html', context)
    
    # Otherwise, return the full page
    return render(request, 'admin/reports/report_detail.html', context)'''
    
    # Replace the function
    updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    # Write the updated content back to the file
    if content != updated_content:
        with open(views_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        print(f"Successfully updated {views_path}")
        return True
    else:
        print("Function not found or no changes made")
        return False

if __name__ == "__main__":
    update_admin_report_view() 