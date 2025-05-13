"""
Module for handling QR code-based violation registration.
This module provides functionality for generating QR codes for violations
and handling user registration with linked violations.
"""

import io
import base64
import uuid
import hashlib
import qrcode
import logging
from datetime import datetime, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.db import transaction
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django import forms

from .models import Violation, ViolationType, UserProfile, ViolatorQRHash

logger = logging.getLogger(__name__)

# QR code hash table - in a real application, this would be stored in the database
# For now, we'll use an in-memory dictionary for simplicity
qr_hash_map = {}

class ExtendedUserCreationForm(UserCreationForm):
    """Extended UserCreationForm with additional fields for registration."""
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    license_number = forms.CharField(required=False)
    address = forms.CharField(required=False, widget=forms.Textarea)
    phone_number = forms.CharField(required=False)
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
    
    def clean_email(self):
        """Validate that the email is not already in use."""
        email = self.cleaned_data.get('email')
        
        # Basic format validation
        if email:
            # Check for @ symbol and proper domain format
            if '@' not in email:
                raise forms.ValidationError("Please enter a valid email address with '@' symbol.")
            
            # Split email into username and domain parts
            parts = email.split('@')
            if len(parts) != 2 or not parts[0] or not parts[1]:
                raise forms.ValidationError("Please enter a valid email address with username and domain.")
            
            # Check domain has at least one dot (for TLD)
            domain = parts[1]
            if '.' not in domain or domain.endswith('.'):
                raise forms.ValidationError("Please enter an email with a valid domain (example@domain.com).")
            
            # Check if email already exists in system
            if User.objects.filter(email__iexact=email).exists():
                # Get the existing user details for logging purposes
                existing_user = User.objects.get(email__iexact=email)
                logger.warning(
                    f"Registration attempt with existing email: {email}. "
                    f"Email belongs to user: {existing_user.username} (ID: {existing_user.id})"
                )
                raise forms.ValidationError("This email address is already registered. Please use a different email or login to your existing account.")
        
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user

def get_or_create_qr_hash(violation):
    """Get or create a QR hash for the given violation."""
    logger.info(f"get_or_create_qr_hash (views_violation_qr.py) called for violation ID: {violation.id}")
    
    # Get violator information from the violator relationship
    if hasattr(violation, 'violator') and violation.violator:
        # Get information from the violator object
        first_name = violation.violator.first_name.strip().lower() if violation.violator.first_name else "unknown"
        last_name = violation.violator.last_name.strip().lower() if violation.violator.last_name else "unknown"
        license_number = violation.violator.license_number.strip().upper().replace(' ', '') if violation.violator.license_number else None
        phone_number = violation.violator.phone_number if hasattr(violation.violator, 'phone_number') else None
        
        logger.info(f"Got violator info from related Violator model for violation {violation.id}")
    else:
        # Fallback to other fields that might exist on the Violation model
        logger.info(f"No violator relationship found for violation {violation.id}, checking direct fields")
        first_name = getattr(violation, 'first_name', getattr(violation, 'driver_name', "unknown"))
        if first_name:
            first_name = first_name.strip().lower()
            # If driver_name contains full name, try to split it
            if ' ' in first_name and not getattr(violation, 'last_name', None):
                name_parts = first_name.split(' ', 1)
                first_name = name_parts[0]
                last_name = name_parts[1]
            else:
                first_name = first_name
                last_name = getattr(violation, 'last_name', "unknown")
        else:
            first_name = "unknown"
            
        last_name = getattr(violation, 'last_name', "unknown")
        if last_name:
            last_name = last_name.strip().lower()
        else:
            last_name = "unknown"
            
        license_number = getattr(violation, 'license_number', None)
        if license_number:
            license_number = license_number.strip().upper().replace(' ', '')
            
        phone_number = getattr(violation, 'phone_number', None)
    
    logger.info(f"Standardized violator info: {first_name} {last_name}, license: {license_number}")
    
    # Additional vehicle information for logging purposes
    vehicle_type = getattr(violation, 'vehicle_type', 'Unknown')
    plate_number = getattr(violation, 'plate_number', 'Unknown')
    logger.info(f"Vehicle info for violation {violation.id}: Type: {vehicle_type}, Plate: {plate_number}")

    # First check if violation already has a QR hash
    if violation.qr_hash:
        logger.info(f"Violation {violation.id} already has QR hash: {violation.qr_hash.hash_id}")
        return violation.qr_hash.hash_id

    # Check for existing QR hash for the violator - FIRST APPROACH: By License + User Account
    logger.info(f"Checking for existing violations and QR hashes for the same violator")
    existing_hash = None
    
    # Try to find by license number first (most reliable)
    if license_number:
        logger.info(f"Looking for existing QR hash by license number: {license_number}")
        
        # Check if another violation with the same license number already has a QR hash
        existing_violation_with_hash = Violation.objects.filter(
            violator__license_number__iexact=license_number,
            qr_hash__isnull=False
        ).first()
        
        if existing_violation_with_hash and existing_violation_with_hash.qr_hash:
            existing_hash = existing_violation_with_hash.qr_hash
            logger.info(f"Found QR hash through another violation with same license: {existing_hash.hash_id}")
        else:
            # If no violation found with same license and QR hash, check QR hash table directly
            existing_hash = ViolatorQRHash.objects.filter(
                license_number__iexact=license_number
            ).first()
            if existing_hash:
                logger.info(f"Found existing QR hash by license in QRHash table: {existing_hash.hash_id}")
    
    # If not found by license, try by name
    if not existing_hash and first_name != "unknown" and last_name != "unknown":
        logger.info(f"Looking for existing QR hash by name: {first_name} {last_name}")
        
        # Check if another violation with the same name already has a QR hash
        existing_violation_with_hash = Violation.objects.filter(
            violator__first_name__iexact=first_name,
            violator__last_name__iexact=last_name,
            qr_hash__isnull=False
        ).first()
        
        if existing_violation_with_hash and existing_violation_with_hash.qr_hash:
            existing_hash = existing_violation_with_hash.qr_hash
            logger.info(f"Found QR hash through another violation with same name: {existing_hash.hash_id}")
        else:
            # If no violation found with same name and QR hash, check QR hash table directly
            existing_hash = ViolatorQRHash.objects.filter(
                first_name__iexact=first_name,
                last_name__iexact=last_name
            ).first()
            if existing_hash:
                logger.info(f"Found existing QR hash by name in QRHash table: {existing_hash.hash_id}")
    
    # If we found an existing QR hash, use it
    if existing_hash:
        logger.info(f"Using existing QR hash {existing_hash.hash_id} for violation {violation.id}")
        
        # Check if this QR hash has linked violations and log them for debugging
        linked_violations = Violation.objects.filter(qr_hash=existing_hash).exclude(id=violation.id)
        if linked_violations.exists():
            logger.info(f"This QR hash is already linked to {linked_violations.count()} other violations")
            for v in linked_violations:
                v_vehicle_type = getattr(v, 'vehicle_type', 'Unknown')
                v_plate = getattr(v, 'plate_number', 'Unknown')
                logger.info(f"Linked violation ID: {v.id}, Vehicle: {v_vehicle_type}, Plate: {v_plate}")
        
        violation.qr_hash = existing_hash
        violation.save()
        return existing_hash.hash_id

    # If no existing hash was found, generate a new one
    logger.info(f"No existing QR hash found, generating new one for {first_name} {last_name}")
    hash_id = ViolatorQRHash.generate_hash(
        first_name=first_name,
        last_name=last_name,
        license_number=license_number
    )
    
    # Create new QR hash with 90-day expiration
    qr_hash = ViolatorQRHash.objects.create(
        hash_id=hash_id,
        first_name=first_name,
        last_name=last_name,
        license_number=license_number,
        phone_number=phone_number,
        expires_at=timezone.now() + timezone.timedelta(days=90)
    )
    logger.info(f"Created new QR hash: {hash_id}")

    # Link it to the violation
    violation.qr_hash = qr_hash
    violation.save()
    logger.info(f"Linked new QR hash to violation {violation.id}")

    return hash_id

def generate_qr_code(hash_id, base_url=None):
    """
    Generate a QR code for a violation hash.
    
    Args:
        hash_id: The hash ID for the violation
        base_url: The base URL for the application
        
    Returns:
        tuple: (bytes, str) The QR code image as bytes and the registration URL
    """
    if base_url is None:
        base_url = settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'http://localhost:8000'
    
    # Create the registration URL with the hash
    # Instead of using reverse, we'll use a hard-coded URL pattern
    registration_url = f"{base_url}/register/violations/{hash_id}/"
    
    # Generate the QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(registration_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert the image to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes = img_bytes.getvalue()
    
    return img_bytes, registration_url

def violation_qr_code_image(request, violation_id):
    """
    Generate and serve a QR code image for a violation.
    
    Args:
        request: The HTTP request
        violation_id: The ID of the violation
        
    Returns:
        HttpResponse: The QR code image as a PNG
    """
    try:
        violation = get_object_or_404(Violation, id=violation_id)
        hash_id = get_or_create_qr_hash(violation)
        qr_img, _ = generate_qr_code(hash_id)
        
        return HttpResponse(qr_img, content_type='image/png')
    except Exception as e:
        logger.error(f"Error generating QR code: {str(e)}")
        return HttpResponse("Error generating QR code", status=500)

def violation_qr_code_print_view(request, violation_id):
    """
    Display a printable page with QR code for a violation ticket.
    
    Args:
        request: The HTTP request
        violation_id: The ID of the violation
        
    Returns:
        HttpResponse: Rendered template with the QR code
    """
    try:
        violation = get_object_or_404(Violation, id=violation_id)
        hash_id = get_or_create_qr_hash(violation)
        qr_img, registration_url = generate_qr_code(hash_id)
        
        # Convert QR code to base64 for embedding in HTML
        qr_code_base64 = base64.b64encode(qr_img).decode('utf-8')
        
        context = {
            'violation': violation,
            'qr_code_base64': qr_code_base64,
            'registration_url': registration_url
        }
        
        return render(request, 'violations/qr_code_print.html', context)
    except Exception as e:
        logger.error(f"Error rendering QR code print view: {str(e)}")
        messages.error(request, "Error generating QR code for printing.")
        return redirect('direct_ticket_form')

def get_violation_qr_info(request, hash_id):
    """
    API endpoint to get information about a violation from its QR hash.
    
    Args:
        request: The HTTP request
        hash_id: The hash ID from the QR code
        
    Returns:
        JsonResponse: Violation information in JSON format
    """
    try:
        # First check the in-memory map
        violation_id = None
        for vid, hid in qr_hash_map.items():
            if hid == hash_id:
                violation_id = int(vid)
                logger.info(f"Found violation ID {violation_id} in memory for hash {hash_id}")
                break
        
        # If not found in memory, check the database
        if violation_id is None:
            try:
                # Look up the QR hash in the database
                qr_hash_obj = ViolatorQRHash.objects.filter(hash_id=hash_id).first()
                if qr_hash_obj:
                    # Find the violation linked to this QR hash
                    violation = Violation.objects.filter(qr_hash=qr_hash_obj).first()
                    if violation:
                        violation_id = violation.id
                        logger.info(f"Found violation ID {violation_id} in database for hash {hash_id}")
            except Exception as e:
                logger.error(f"Error looking up QR hash in database: {str(e)}")
        
        if violation_id is None:
            logger.warning(f"QR hash {hash_id} not found in memory or database")
            return JsonResponse({'error': 'Invalid or expired QR code'}, status=400)
        
        violation = get_object_or_404(Violation, id=violation_id)
        
        return JsonResponse({
            'violation_id': violation.id,
            'ticket_number': violation.ticket_number,
            'date_of_violation': violation.date_of_violation.strftime('%Y-%m-%d %H:%M'),
            'violation_type': violation.violation_type.name,
            'location': violation.location,
            'fine_amount': float(violation.violation_type.violation_fee),
            'status': violation.status
        })
    except Exception as e:
        logger.error(f"Error retrieving violation QR info: {str(e)}")
        return JsonResponse({'error': 'Error retrieving violation information'}, status=500)

def register_with_violations(request, hash_id=None):
    """
    View for users to register an account and link to existing violations.
    This is called from the QR code scan.
    """
    logger.info(f"Processing registration with violations for hash_id: {hash_id}")
    
    # Variables to keep track of what we've found
    violations_linked = []
    qr_hash = None
    
    # First, check if the hash_id exists and get associated violations
    try:
        if hash_id:
            # Try to get the QR hash record
            qr_hash = ViolatorQRHash.objects.get(hash_id=hash_id)
            logger.info(f"Found QR hash record for {hash_id}")
            
            # Check if it's already registered to a user account
            if qr_hash.registered and qr_hash.user_account:
                logger.warning(f"QR hash {hash_id} already registered to user {qr_hash.user_account.username}")
                messages.warning(
                    request, 
                    "This QR code has already been registered. Please log in to access your violations."
                )
                return redirect('login')
            
            # Get violations linked to this hash
            violations_linked = Violation.objects.filter(qr_hash=qr_hash)
            logger.info(f"Found {violations_linked.count()} violations linked to hash {hash_id}")
    except ViolatorQRHash.DoesNotExist:
        logger.error(f"QR hash {hash_id} not found")
        messages.error(request, "Invalid or expired QR code. Please contact the traffic enforcement office.")
        return redirect('login')
    except Exception as e:
        # Log the error and show a user-friendly message
        logger.error(f"Error checking QR hash {hash_id}: {str(e)}")
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('login')
    
    if not violations_linked:
        logger.error(f"No violations found for hash {hash_id}")
        messages.error(request, "Invalid or expired QR code. Please contact the traffic enforcement office.")
        return redirect('login')
        
    if request.method == 'POST':
        logger.info(f"Processing POST request for hash {hash_id}")
        form = ExtendedUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = None
                # Use a separate transaction for user creation and profile setup
                with transaction.atomic():
                    user = form.save()
                    
                    # Create or update user profile
                    # The UserProfile might already be created by a signal or other process
                    profile, created = UserProfile.objects.get_or_create(
                        user=user,
                        defaults={
                            'role': 'VIOLATOR',
                            'is_email_verified': False
                        }
                    )
                    
                    # Update profile with form data
                    license_number = form.cleaned_data.get('license_number')
                    logger.info(f"Form license number: {license_number}")
                    
                    # Standardize the license number (remove spaces, uppercase, etc.)
                    if license_number:
                        license_number = license_number.strip().upper().replace(' ', '')
                    
                    # Update profile with additional fields
                    profile.license_number = license_number
                    profile.address = form.cleaned_data.get('address', '')
                    profile.phone_number = form.cleaned_data.get('phone_number', '')
                    profile.save()
                    logger.info(f"Updated profile for user {user.username} with additional data")
                    
                    # Mark the QR hash as registered and link it to the user
                    qr_hash.registered = True
                    qr_hash.user_account = user
                    qr_hash.save()
                    
                    # Link all violations to the user
                    violations_count = 0
                    for violation in violations_linked:
                        # Only link violations that aren't already linked to a user
                        if not violation.user_account:
                            violation.user_account = user
                            violation.save()
                            violations_count += 1
                    
                    logger.info(f"Linked {violations_count} violations to user {user.username}")
                
                # Log in the new user
                raw_password = form.cleaned_data.get('password1')
                user = authenticate(username=user.username, password=raw_password)
                login(request, user)
                
                # Send a notification mail to the driver about successful registration
                # try:
                #     send_registration_notification_email(user, qr_hash, violations_linked)
                # except Exception as e:
                #     logger.error(f"Error sending notification email: {str(e)}")
                
                # Show a success message
                messages.success(request, "Your account has been created successfully. Please verify your email address.")
                return redirect('user_portal:dashboard')
                
            except Exception as e:
                logger.error(f"Error creating user account: {str(e)}")
                messages.error(request, f"An error occurred: {str(e)}")
                return redirect('login')
        else:
            # If the form is not valid, log the errors
            logger.warning(f"Invalid form submission: {form.errors}")
    else:
        # Create the form with initial data from the QR hash
        initial = {}
        if qr_hash:
            if qr_hash.first_name and qr_hash.first_name != 'unknown':
                initial['first_name'] = qr_hash.first_name.title()
            if qr_hash.last_name and qr_hash.last_name != 'unknown':
                initial['last_name'] = qr_hash.last_name.title()
            if qr_hash.license_number:
                initial['license_number'] = qr_hash.license_number
            if qr_hash.phone_number:
                initial['phone_number'] = qr_hash.phone_number
                
        # Also try to get data from the violations
        if violations_linked and not initial.get('first_name'):
            violation = violations_linked.first()
            
            if hasattr(violation, 'violator') and violation.violator:
                if violation.violator.first_name:
                    initial['first_name'] = violation.violator.first_name.title()
                if violation.violator.last_name:
                    initial['last_name'] = violation.violator.last_name.title()
                if violation.violator.license_number:
                    initial['license_number'] = violation.violator.license_number
                if hasattr(violation.violator, 'phone_number') and violation.violator.phone_number:
                    initial['phone_number'] = violation.violator.phone_number
                if hasattr(violation.violator, 'address') and violation.violator.address:
                    initial['address'] = violation.violator.address
                    
        form = ExtendedUserCreationForm(initial=initial)
        logger.info(f"Created form with initial data: {initial}")
        
        # Add Bootstrap classes to form fields
        for field_name, field in form.fields.items():
            field.widget.attrs['class'] = 'form-control'
    
    # Get violations associated with the hash
    violations_list = violations_linked
    logger.info(f"Rendering registration template with {len(violations_list)} violations")
    for v in violations_list:
        logger.info(f"Violation in context: ID={v.id}, Type={v.violation_type}, Amount={v.fine_amount}")
    
    # Log final context being sent to template
    logger.info(f"Template context: hash_id={hash_id}, violations_count={len(violations_list)}")
    
    return render(request, 'registration/register_with_violations.html', {
            'form': form,
        'violations': violations_list,
            'hash_id': hash_id
    })

def register_with_direct_violation(request, violation_id):
    """Register a new user with a direct violation ID."""
    logger.info(f"register_with_direct_violation called for violation ID: {violation_id}")
    
    # Get the violation
    try:
        violation = Violation.objects.get(pk=violation_id)
        logger.info(f"Found violation ID: {violation.id}, status: {violation.status}")
        
        # Check if this violation is already linked to a user account
        if violation.user_account:
            logger.warning(f"Violation {violation_id} is already linked to user: {violation.user_account.username}")
            messages.warning(request, 
                "This violation is already linked to an account. Please log in to that account, or contact support if you need assistance."
            )
            return redirect('login')
            
        # Check if the violation has a QR hash
        if violation.qr_hash:
            hash_id = violation.qr_hash.hash_id
            logger.info(f"Violation has QR hash: {hash_id}, registered: {violation.qr_hash.registered}")
            
            # Check if this QR hash is already registered
            if violation.qr_hash.registered:
                logger.warning(f"QR hash {hash_id} for violation {violation_id} is already registered")
                messages.warning(request, 
                    "This violation's QR code has already been registered. Please log in to view your violations, or contact support if you need assistance."
                )
                return redirect('login')
                
            # Check if this QR hash is linked to a user account
            if violation.qr_hash.user_account:
                logger.warning(f"QR hash {hash_id} for violation {violation_id} is already linked to user: {violation.qr_hash.user_account.username}")
                messages.warning(request, 
                    "This violation is already linked to an account. Please log in to that account, or contact support if you need assistance."
                )
                return redirect('login')
                
            # Check how many violations are linked to this QR hash
            linked_violations = list(violation.qr_hash.violations.all())
            violation_count = len(linked_violations)
            logger.info(f"QR hash {hash_id} has {violation_count} linked violations")
            
    except Violation.DoesNotExist:
        logger.warning(f"Violation not found: {violation_id}")
        messages.error(request, "Invalid violation ID. Please try again or contact support.")
        return redirect('login')
    except Exception as e:
        logger.error(f"Error checking violation {violation_id}: {str(e)}")
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('login') 
    
    # Use the hash_id to redirect to the register_with_violations view
    hash_id = violation.qr_hash.hash_id if violation.qr_hash else get_or_create_qr_hash(violation)
    logger.info(f"Redirecting to register_with_violations with hash: {hash_id}")
    return redirect('register_with_violations', hash_id=hash_id) 

def issue_direct_ticket(request, violation_id):
    """Register a new user with a direct violation ID."""
    logger.info(f"issue_direct_ticket called for violation ID: {violation_id}")
    
    # Get the violation
    try:
        violation = Violation.objects.get(pk=violation_id)
        logger.info(f"Found violation ID: {violation.id}, status: {violation.status}")
        
        # Check if this violation is already linked to a user account
        if violation.user_account:
            logger.warning(f"Violation {violation_id} is already linked to user: {violation.user_account.username}")
            messages.warning(request, 
                "This violation is already linked to an account. Please log in to that account, or contact support if you need assistance."
            )
            return redirect('login')
            
        # Check if the violation has a QR hash
        if violation.qr_hash:
            hash_id = violation.qr_hash.hash_id
            logger.info(f"Violation has QR hash: {hash_id}, registered: {violation.qr_hash.registered}")
            
            # Check if this QR hash is already registered
            if violation.qr_hash.registered:
                logger.warning(f"QR hash {hash_id} for violation {violation_id} is already registered")
                messages.warning(request, 
                    "This violation's QR code has already been registered. Please log in to view your violations, or contact support if you need assistance."
                )
                return redirect('login')
                
            # Check if this QR hash is linked to a user account
            if violation.qr_hash.user_account:
                logger.warning(f"QR hash {hash_id} for violation {violation_id} is already linked to user: {violation.qr_hash.user_account.username}")
                messages.warning(request, 
                    "This violation is already linked to an account. Please log in to that account, or contact support if you need assistance."
                )
                return redirect('login')
                
            # Check how many violations are linked to this QR hash
            linked_violations = list(violation.qr_hash.violations.all())
            violation_count = len(linked_violations)
            logger.info(f"QR hash {hash_id} has {violation_count} linked violations")
            
    except Violation.DoesNotExist:
        logger.warning(f"Violation not found: {violation_id}")
        messages.error(request, "Invalid violation ID. Please try again or contact support.")
        return redirect('login')
    except Exception as e:
        logger.error(f"Error checking violation {violation_id}: {str(e)}")
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('login') 
    
    # Use the hash_id to redirect to the register_with_violations view
    hash_id = violation.qr_hash.hash_id if violation.qr_hash else get_or_create_qr_hash(violation)
    logger.info(f"Redirecting to register_with_violations with hash: {hash_id}")
    return redirect('register_with_violations', hash_id=hash_id) 