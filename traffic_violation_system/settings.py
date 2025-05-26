from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Import crypto utilities for handling encrypted environment variables
try:
    from CAPSTONE_PROJECT.crypto_utils import get_env_value
except ImportError:
    # Fallback if crypto_utils is not available
    def get_env_value(name, default=None):
        return os.environ.get(name, default)

# Use environment variables for sensitive data
BREVO_API_KEY = get_env_value('BREVO_API_KEY')
DEFAULT_FROM_EMAIL = get_env_value('DEFAULT_FROM_EMAIL')
SITE_URL = get_env_value('SITE_URL', 'http://localhost:8000')

# Email verification settings
EMAIL_VERIFICATION_REQUIRED = True
EMAIL_VERIFICATION_TIMEOUT_HOURS = int(get_env_value('EMAIL_VERIFICATION_TIMEOUT_HOURS', 24))
EMAIL_VERIFICATION_CODE_LENGTH = int(get_env_value('EMAIL_VERIFICATION_CODE_LENGTH', 6))

# File Storage
DEFAULT_FILE_STORAGE = 'traffic_violation_system.storage.SafeFileStorage'

# Maximum filename length
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB limit 