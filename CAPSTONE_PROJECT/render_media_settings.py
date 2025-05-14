import os
from pathlib import Path
import logging
from .settings import *

# Configure logging
logger = logging.getLogger(__name__)
logger.info("Loading Render Media-optimized settings")

# Set Render environment variable
os.environ['RENDER'] = 'True'

# Debug should be False in production
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Update secret key from environment
SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-secret-key-for-build-not-for-production')

# Allow all hostnames from Render
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '.onrender.com,localhost').split(',')

# Configure Render's persistent storage for media
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join('/opt/render/project/src/', 'media')

# Create media root if it doesn't exist
if not os.path.exists(MEDIA_ROOT):
    try:
        os.makedirs(MEDIA_ROOT, exist_ok=True)
        logger.info(f"Created MEDIA_ROOT directory: {MEDIA_ROOT}")
        
        # Create common subdirectories
        for subdir in [
            'avatars', 'qr_codes', 'vehicle_documents', 
            'violation_evidence', 'driver_documents', 'signatures',
            'barangay_certificate', 'cedula', 'cenro_tickets',
            'driver_applications', 'driver_photos', 'educational',
            'educational_topics', 'mayors_permits', 'operator_docs'
        ]:
            os.makedirs(os.path.join(MEDIA_ROOT, subdir), exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create media directories: {str(e)}")

# Configure static files with WhiteNoise
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Insert WhiteNoise middleware for static files
if 'whitenoise.middleware.WhiteNoiseMiddleware' not in MIDDLEWARE:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Use the SafeFileStorage for better file handling
DEFAULT_FILE_STORAGE = 'traffic_violation_system.storage.SafeFileStorage'

# Set up more detailed logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join('/opt/render/project/src/', 'app.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'traffic_violation_system': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    },
}

# Database configuration - using SQLite initially, can be replaced with PostgreSQL
if 'DATABASE_URL' in os.environ:
    # Use PostgreSQL if DATABASE_URL is provided by Render
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
    logger.info("Using PostgreSQL database from DATABASE_URL")
else:
    # Fallback to SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }
    logger.info("Using SQLite database (fallback)")

# Security settings
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False 