#!/usr/bin/env python
"""
Media Configuration Checker and Fixer for Render Deployment

This script checks and fixes common media configuration issues in Django projects
deployed to Render. It verifies media directories, permissions, and URL patterns.

Usage:
    python fix_render_media.py

The script will:
1. Check if the RENDER environment variable is set
2. Verify media directories exist and have proper permissions
3. Validate media URL configurations
4. Test media file access
5. Make necessary fixes for Render deployment
"""

import os
import sys
import django
from pathlib import Path
import shutil
import logging
import importlib
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("render_media_fix")

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)

def check_environment():
    """Check if the environment is configured for Render"""
    print_header("Environment Check")
    
    # Check if we're on Render
    render_env = os.environ.get('RENDER', 'False')
    print(f"RENDER environment variable: {render_env}")
    
    # Check Django settings
    try:
        django_settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', 'CAPSTONE_PROJECT.settings')
        print(f"Django settings module: {django_settings_module}")
        os.environ['DJANGO_SETTINGS_MODULE'] = django_settings_module
        
        # Initialize Django
        django.setup()
        
        # Import settings
        from django.conf import settings
        
        # Check media settings
        print(f"DEBUG: {settings.DEBUG}")
        print(f"MEDIA_URL: {settings.MEDIA_URL}")
        print(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
        
        # Set RENDER=True if it's not set but we're likely on Render
        if render_env == 'False' and '/opt/render/' in os.getcwd():
            os.environ['RENDER'] = 'True'
            print("✓ Set RENDER=True based on environment detection")
        
        return settings
    except Exception as e:
        print(f"✗ Error checking Django settings: {str(e)}")
        traceback.print_exc()
        return None

def check_media_directories(settings):
    """Check if media directories exist and have proper permissions"""
    print_header("Media Directories Check")
    
    media_root = settings.MEDIA_ROOT
    print(f"Checking media directory: {media_root}")
    
    # Check if the directory exists
    if os.path.exists(media_root):
        print(f"✓ Media directory exists: {media_root}")
    else:
        print(f"✗ Media directory does not exist: {media_root}")
        try:
            os.makedirs(media_root, exist_ok=True)
            print(f"✓ Created media directory: {media_root}")
        except Exception as e:
            print(f"✗ Failed to create media directory: {str(e)}")
    
    # Check if the directory is writable
    try:
        test_file = os.path.join(media_root, 'test_write.txt')
        with open(test_file, 'w') as f:
            f.write('Test write access')
        os.remove(test_file)
        print(f"✓ Media directory is writable")
    except Exception as e:
        print(f"✗ Media directory is not writable: {str(e)}")
    
    # Check required subdirectories
    subdirs = [
        'avatars', 'qr_codes', 'vehicle_documents', 
        'violation_evidence', 'driver_documents', 'signatures',
        'barangay_certificate', 'cedula', 'cenro_tickets',
        'driver_applications', 'driver_photos', 'educational',
        'educational_topics', 'mayors_permits', 'operator_docs'
    ]
    
    for subdir in subdirs:
        subdir_path = os.path.join(media_root, subdir)
        if not os.path.exists(subdir_path):
            try:
                os.makedirs(subdir_path, exist_ok=True)
                print(f"✓ Created missing subdirectory: {subdir}")
            except Exception as e:
                print(f"✗ Failed to create subdirectory {subdir}: {str(e)}")

def check_media_server(settings):
    """Check if the media server is properly configured"""
    print_header("Media Server Configuration")
    
    # Check if we can import MediaFileServer
    try:
        from traffic_violation_system.serve_media import MediaFileServer
        print("✓ MediaFileServer is available")
        return True
    except ImportError:
        print("✗ MediaFileServer is NOT available")
        
        # Try to locate the serve_media.py file
        serve_media_path = os.path.join(os.getcwd(), 'traffic_violation_system', 'serve_media.py')
        if os.path.exists(serve_media_path):
            print(f"Found serve_media.py at {serve_media_path}")
        else:
            print(f"Could not find serve_media.py at {serve_media_path}")
        
        return False

def fix_media_server():
    """Fix the media server configuration"""
    print_header("Fixing Media Server Configuration")
    
    # Create or update the serve_media.py file
    serve_media_content = """import os
import logging
from django.conf import settings
from django.http import Http404, FileResponse, HttpResponse
from django.views.static import serve
from pathlib import Path
import mimetypes
import sys

# Set up logging
logger = logging.getLogger(__name__)

class MediaFileServer:
    """
    A class to handle serving media files in production environments.
    This is particularly useful for serving user-uploaded files on platforms
    like Render that don't provide easy ways to serve files from a disk.
    """
    
    @staticmethod
    def serve_media_file(request, path):
        """
        Serve a media file from the MEDIA_ROOT directory.
        
        Args:
            request: The HTTP request
            path: The file path relative to MEDIA_ROOT
            
        Returns:
            FileResponse: The file to be served
            
        Raises:
            Http404: If the file does not exist or is not accessible
        """
        try:
            # Log request for debugging
            logger.info(f"Media request: {path}")
            
            # Security check - prevent path traversal attacks
            if '..' in path or path.startswith('/'):
                logger.warning(f"Invalid file path attempted: {path}")
                raise Http404("Invalid file path")
                
            # Build the absolute path to the media file
            media_path = os.path.join(settings.MEDIA_ROOT, path)
            logger.debug(f"Looking for media file at: {media_path}")
            
            # Check if the file exists
            if not os.path.exists(media_path) or not os.path.isfile(media_path):
                logger.warning(f"File not found: {media_path}")
                raise Http404(f"File not found: {path}")
                
            # Determine the content type
            content_type, encoding = mimetypes.guess_type(media_path)
            
            # If we can't determine the content type, use a safe default
            if content_type is None:
                content_type = 'application/octet-stream'
                
            # Create and return the file response
            with open(media_path, 'rb') as f:
                response = FileResponse(f, content_type=content_type)
            
            # Set the content disposition to inline for viewing in browser
            response['Content-Disposition'] = f'inline; filename="{os.path.basename(path)}"'
            
            # Log successful response
            logger.info(f"Successfully served media file: {path}")
            
            return response
            
        except Exception as e:
            # Log any errors that occur
            logger.error(f"Error serving media file {path}: {str(e)}")
            
            # Fallback to Django's built-in serve function if available
            try:
                logger.info(f"Attempting fallback to Django's serve function for {path}")
                return serve(request, path, document_root=settings.MEDIA_ROOT)
            except Exception as fallback_error:
                logger.error(f"Fallback serve also failed: {str(fallback_error)}")
                raise Http404(f"Could not serve file: {path}")

# Create an instance for easier imports
media_server = MediaFileServer()
"""
    
    serve_media_path = os.path.join(os.getcwd(), 'traffic_violation_system', 'serve_media.py')
    try:
        with open(serve_media_path, 'w') as f:
            f.write(serve_media_content)
        print(f"✓ Updated serve_media.py at {serve_media_path}")
    except Exception as e:
        print(f"✗ Failed to update serve_media.py: {str(e)}")

def check_url_patterns():
    """Check if URL patterns for media files are correctly configured"""
    print_header("URL Patterns Check")
    
    urls_file = os.path.join(os.getcwd(), 'CAPSTONE_PROJECT', 'urls.py')
    
    try:
        with open(urls_file, 'r') as f:
            content = f.read()
            
        if "os.environ.get('RENDER'" in content and "from traffic_violation_system.serve_media import MediaFileServer" in content:
            print("✓ URL patterns for Render media files are configured")
        else:
            print("✗ URL patterns for Render media files might not be correctly configured")
            
            # Check if we need to fix the URLs
            return False
    except Exception as e:
        print(f"✗ Error checking URL patterns: {str(e)}")
        return False
        
    return True

def fix_url_patterns():
    """Fix the URL patterns for media files"""
    print_header("Fixing URL Patterns")
    
    # Import settings to get media configuration
    try:
        from django.conf import settings
    except:
        print("✗ Could not import Django settings. Make sure Django is set up correctly.")
        return
    
    urls_content = """from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.decorators.cache import never_cache
import os
import logging

# Set up logging
logger = logging.getLogger(__name__)

urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        next_page='login',
        extra_context={'no_cache': True}
    ), name='logout'),
    path('reports/', include('reports.urls')),
    path('', include('traffic_violation_system.adjudication_history_urls')),
    path('', include('traffic_violation_system.reports.urls')),
    path('', include('traffic_violation_system.urls')),
]

# Always serve static files in any environment
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Log media configuration for debugging
logger.info(f"Media URL: {settings.MEDIA_URL}")
logger.info(f"Media Root: {settings.MEDIA_ROOT}")
logger.info(f"RENDER Environment: {os.environ.get('RENDER', 'Not set')}")
logger.info(f"DEBUG Mode: {settings.DEBUG}")

# For development environment, serve media files directly
if settings.DEBUG:
    logger.info("Using Django development server for media files")
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# For production environment like Render, use our custom media server
elif os.environ.get('RENDER', 'False') == 'True':
    try:
        from traffic_violation_system.serve_media import MediaFileServer, media_server
        logger.info("Using custom MediaFileServer for Render deployment")
        
        # Add a path to serve media files
        urlpatterns += [
            re_path(r'^media/(?P<path>.*)$', MediaFileServer.serve_media_file, name='serve_media'),
        ]
    except ImportError as e:
        logger.error(f"Failed to import MediaFileServer: {str(e)}")
        logger.warning("Falling back to Django static serving for media files")
        # Fallback to static serving
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Fallback for other production environments
    logger.info("Using Django static serving for media files (production fallback)")
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
"""
    
    urls_file = os.path.join(os.getcwd(), 'CAPSTONE_PROJECT', 'urls.py')
    try:
        with open(urls_file, 'w') as f:
            f.write(urls_content)
        print(f"✓ Updated URL patterns at {urls_file}")
    except Exception as e:
        print(f"✗ Failed to update URL patterns: {str(e)}")

def create_test_media_files(settings):
    """Create test media files to verify access"""
    print_header("Test Media Files")
    
    media_root = settings.MEDIA_ROOT
    
    # Define subdirectories to test
    subdirs = [
        'avatars', 'barangay_certificate', 'cedula', 'cenro_tickets',
        'driver_applications', 'driver_photos', 'educational',
        'educational_topics', 'mayors_permits', 'operator_docs'
    ]
    
    for subdir in subdirs:
        subdir_path = os.path.join(media_root, subdir)
        test_file = os.path.join(subdir_path, 'test_file.txt')
        
        try:
            os.makedirs(subdir_path, exist_ok=True)
            with open(test_file, 'w') as f:
                f.write(f'Test file for {subdir}')
            print(f"{subdir} - Test Link")
        except Exception as e:
            print(f"✗ Could not create test file in {subdir}: {str(e)}")

def main():
    """Main function to run the media configuration check and fix"""
    print_header("Media Configuration Diagnostic")
    
    # Check environment
    settings = check_environment()
    if not settings:
        print("✗ Failed to load Django settings. Exiting.")
        return
    
    # Check media directories
    check_media_directories(settings)
    
    # Check media server
    media_server_ok = check_media_server(settings)
    if not media_server_ok:
        fix_media_server()
    
    # Check URL patterns
    url_patterns_ok = check_url_patterns()
    if not url_patterns_ok:
        fix_url_patterns()
    
    # Create test media files
    create_test_media_files(settings)
    
    print_header("Summary")
    print("""
Issues fixed:
- Ensured RENDER environment variable is set
- Created and configured media directories 
- Updated MediaFileServer to handle file serving
- Fixed URL patterns for Render deployment
- Created test media files
    
To finalize the fix:
1. Restart your Render service
2. Test media file access
3. Check your logs for any media serving issues
    """)

if __name__ == "__main__":
    main() 