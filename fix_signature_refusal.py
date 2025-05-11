"""
Fix for Signature Refusal Feature

This script describes the changes needed to properly store and display the reason
when a violator refuses to sign a violation ticket.

The issue:
1. The frontend form in issue_direct_ticket.html already has UI for signature refusal
2. The issue_direct_ticket.py view is already handling this data properly
3. The violation model already has the necessary fields (signature_refused and refusal_note)
4. However, the main issue_ticket view in views.py is not handling signature refusal properly

Changes required:
1. Update views.py to handle signature refusal data
2. Update ticket_data dictionary to include signature_refusal information

Implementation steps:
"""

# 1. Update views.py to handle signature refusal data
# Find the issue_ticket function in views.py (around line 9685)
# Before the part that handles the signature, add this code:

"""
            # Handle signature refusal if applicable
            signature_refused = request.POST.get('signature_refused') == 'true'
            if signature_refused:
                violation.signature_refused = True
                violation.refusal_note = request.POST.get('refusal_note', '')
                print(f"Violator refused to sign: {violation.refusal_note}")
                signature_data = None
                violation.save()
            else:
                # Initialize signature_data as None
                signature_data = None

                # Handle signature if provided
                signature_input = request.POST.get('signature_data')
                if signature_input:
                    # Existing signature handling code continues...
"""

# 2. Update the ticket_data dictionary in views.py to include signature refusal information
# Find the ticket_data dictionary creation (around line 9815) and add these fields:

"""
            ticket_data = {
                'id': violation.id,
                'first_name': violator.first_name,
                'last_name': violator.last_name,
                # Other existing fields...
                
                # Add these fields:
                'signature_refused': violation.signature_refused,
                'refusal_note': violation.refusal_note or '',
                
                # Continue with existing fields...
                'enforcer_name': request.user.get_full_name(),
                'enforcer_id': request.user.userprofile.enforcer_id
            }
"""

# The violation_detail.html template has already been updated to display the refusal information
# when a signature was refused:

"""
    <!-- Signature Refusal Information (Only displayed when signature was refused) -->
    {% if violation.signature_refused %}
    <div class="card shadow mt-4">
        <div class="card-header bg-warning text-dark">
            <h5 class="card-title mb-0">
                <i class="fas fa-exclamation-triangle me-2"></i>Signature Refused
            </h5>
        </div>
        <div class="card-body">
            <h6 class="font-weight-bold">Reason for Refusal:</h6>
            <div class="p-3 bg-light rounded">
                {{ violation.refusal_note|default:"No reason provided"|linebreaks }}
            </div>
            <small class="text-muted mt-2 d-block">
                <i class="fas fa-info-circle me-1"></i>
                The violator refused to sign the violation ticket.
            </small>
        </div>
    </div>
    {% endif %}
"""

# With these changes, the signature refusal information should now be properly:
# 1. Captured from the form
# 2. Stored in the database
# 3. Displayed on the violation detail page 