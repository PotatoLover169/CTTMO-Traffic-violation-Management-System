import os
from pathlib import Path
from .settings import *
import logging

# Configure logging
logger = logging.getLogger(__name__)
logger.info("Loading Render-specific settings")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Update secret key from environment
SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-secret-key-for-build-not-for-production')

# Allow all hostnames from Render
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '.onrender.com,localhost').split(',')

# Use SQLite for initial deployment testing
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Static and Media files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Always set the RENDER environment variable to True in this settings file
os.environ['RENDER'] = 'True'
logger.info("Set RENDER environment variable to True")

# On Render, we need to use a persistent directory for media files
# This is because the dyno filesystem is ephemeral
MEDIA_URL = '/media/'

# Use a persistent directory on Render
MEDIA_ROOT = os.path.join('/opt/render/project/src/', 'media')
logger.info(f"Configured MEDIA_ROOT to: {MEDIA_ROOT}")

# Ensure the media directory exists
if not os.path.exists(MEDIA_ROOT):
    try:
        os.makedirs(MEDIA_ROOT, exist_ok=True)
        logger.info(f"Created MEDIA_ROOT directory: {MEDIA_ROOT}")
    except Exception as e:
        logger.error(f"Failed to create MEDIA_ROOT directory: {str(e)}")

# Configure WhiteNoise for static files
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# Use the SafeFileStorage for better file handling
DEFAULT_FILE_STORAGE = 'traffic_violation_system.storage.SafeFileStorage'

# Disable security settings for initial testing
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Set up logging with more detailed file logging
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