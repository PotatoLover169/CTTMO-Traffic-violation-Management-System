"""
Configuration validation module for the Traffic Violation System.
This module checks that all required environment variables are set.
"""
import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Define required environment variables
CRITICAL_VARS = [
    'SECRET_KEY',
    'BREVO_API_KEY',
    'ID_ANALYZER_API_KEY',
    'RECAPTCHA_SITE_KEY',
    'RECAPTCHA_SECRET_KEY',
]

# Define recommended environment variables
RECOMMENDED_VARS = [
    'ID_ANALYZER_RESTRICTED_KEY',
    'DEFAULT_FROM_EMAIL',
    'SITE_URL',
    'DEBUG',
    'ALLOWED_HOSTS',
]

def validate_config() -> Dict[str, List[str]]:
    """
    Validate that all required environment variables are set.
    Returns a dictionary with missing and recommended variables.
    """
    missing = []
    recommended = []
    
    # Check critical variables
    for var in CRITICAL_VARS:
        if not os.environ.get(var):
            missing.append(var)
    
    # Check recommended variables
    for var in RECOMMENDED_VARS:
        if not os.environ.get(var):
            recommended.append(var)
    
    return {
        'missing': missing,
        'recommended': recommended
    }

def check_config(raise_exception: bool = False) -> bool:
    """
    Check configuration and log warnings or raise exceptions for missing variables.
    
    Args:
        raise_exception: If True, raise an exception for missing critical variables
        
    Returns:
        bool: True if all critical variables are set, False otherwise
    """
    result = validate_config()
    
    # Log missing critical variables
    if result['missing']:
        error_msg = f"Missing critical environment variables: {', '.join(result['missing'])}"
        logger.error(error_msg)
        if raise_exception:
            raise EnvironmentError(error_msg)
        return False
    
    # Log missing recommended variables
    if result['recommended']:
        logger.warning(f"Missing recommended environment variables: {', '.join(result['recommended'])}")
    
    # Log success if everything is set
    if not result['missing'] and not result['recommended']:
        logger.info("All environment variables are properly configured.")
    elif not result['missing']:
        logger.info("All critical environment variables are properly configured.")
    
    return True

def mask_sensitive_value(value: Optional[str]) -> str:
    """
    Mask a sensitive value for safe logging.
    
    Args:
        value: The sensitive string to mask
        
    Returns:
        str: A masked version of the string
    """
    if not value:
        return "Not set"
    
    if len(value) <= 8:
        return "****"
    
    # Show first 4 and last 4 characters
    return f"{value[:4]}...{value[-4:]}"

def log_config_summary() -> None:
    """Log a summary of the current configuration with masked sensitive values."""
    logger.info("Configuration Summary:")
    
    # Log critical variables (masked)
    for var in CRITICAL_VARS:
        value = os.environ.get(var, "")
        logger.info(f"  {var}: {mask_sensitive_value(value)}")
    
    # Log recommended variables (masked for sensitive ones)
    for var in RECOMMENDED_VARS:
        value = os.environ.get(var, "")
        if "KEY" in var or "SECRET" in var:
            logger.info(f"  {var}: {mask_sensitive_value(value)}")
        else:
            logger.info(f"  {var}: {value or 'Not set'}") 