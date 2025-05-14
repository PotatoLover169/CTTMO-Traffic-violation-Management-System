import os
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