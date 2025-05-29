from django import template
from datetime import datetime, date
from decimal import Decimal

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary using key
    Usage: {{ my_dict|get_item:'key' }}
    """
    if key in dictionary:
        return dictionary[key]
    return None

@register.filter
def mul(value, arg):
    """
    Multiply the value by the argument
    Usage: {{ value|mul:5 }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """
    Divide the value by the argument
    Usage: {{ value|div:arg }}
    """
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def floordiv(value, arg):
    """
    Perform integer division (floor division)
    Usage: {{ value|floordiv:5 }}
    """
    try:
        return int(float(value) // float(arg))
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def sub(value, arg):
    """
    Subtract the argument from the value
    Usage: {{ value|sub:arg }}
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def currency(value):
    """Format a value as currency."""
    try:
        # Convert to Decimal for consistent formatting
        decimal_value = Decimal(str(value))
        return f"₱{decimal_value:,.2f}"
    except (ValueError, TypeError):
        return value

@register.filter
def days_since(value, reference_date):
    """Calculate the number of days between a date and reference date (typically today's date)."""
    if not value or not reference_date:
        return 0
    
    # Ensure both are date objects
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(reference_date, datetime):
        reference_date = reference_date.date()
    
    # Calculate difference in days
    difference = (reference_date - value).days
    
    # Return positive number
    return abs(difference)

@register.filter
def percentage(value, total):
    """Calculate the percentage of a value relative to a total."""
    if not value or not total or total == 0:
        return 0
    
    try:
        return int((float(value) / float(total)) * 100)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0 