# Media Configuration Troubleshooting on Render

This guide will help you troubleshoot and fix media file serving issues with your Django application on Render.

## Common Issues

1. **Media files not displaying**: Images, documents, and other media files that were uploaded don't appear when accessed via URLs.
2. **404 errors** when accessing media files
3. **Server errors** when trying to upload or access media files
4. **Incorrect paths** in media file URLs
5. **Permissions issues** with the media directory

## Check Your Configuration

### Environment Variables

First, check if the `RENDER` environment variable is properly set:

```python
import os
print(f"RENDER: {os.environ.get('RENDER', 'Not set')}")
print(f"DEBUG: {os.environ.get('DEBUG', 'Not set')}")
```

### Media Settings

Verify your media settings are correct:

```python
from django.conf import settings
print(f"MEDIA_URL: {settings.MEDIA_URL}")
print(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
```

### Media Directory

Check if your media directory exists and is writable:

```python
import os
from django.conf import settings

media_root = settings.MEDIA_ROOT
print(f"Media directory exists: {os.path.exists(media_root)}")
print(f"Media directory is writable: {os.access(media_root, os.W_OK)}")
```

## Fixes for Render

### 1. Use the Correct Settings Module

Make sure your `render.yaml` is using the media-optimized settings module:

```yaml
envVars:
  - key: DJANGO_SETTINGS_MODULE
    value: CAPSTONE_PROJECT.render_media_settings
```

### 2. Configure Persistent Disk

Ensure you have a persistent disk configured in your `render.yaml`:

```yaml
disk:
  name: media
  mountPath: /opt/render/project/src/media
  sizeGB: 10
```

### 3. Set Environment Variables

Make sure these environment variables are set:

```yaml
envVars:
  - key: RENDER
    value: "True"
  - key: MEDIA_URL
    value: "/media/"
```

### 4. Use Proper URL Patterns

Your URL patterns should include the MediaFileServer for Render:

```python
# For production environment like Render, use our custom media server
elif os.environ.get('RENDER', 'False') == 'True':
    try:
        from traffic_violation_system.serve_media import MediaFileServer
        
        # Add a path to serve media files
        urlpatterns += [
            re_path(r'^media/(?P<path>.*)$', MediaFileServer.serve_media_file, name='serve_media'),
        ]
    except ImportError:
        # Fallback to static serving
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

### 5. Run the Fix Script

If you're still having issues, run the fix script:

```bash
python fix_render_media.py
```

This script will:
- Check and set environment variables
- Verify media directories exist and are writable
- Ensure MediaFileServer is properly configured
- Create test media files
- Fix URL patterns if needed

## Testing Media Files

You can test media file access by adding test files to each directory:

```python
import os
from django.conf import settings

# Define subdirectories to test
subdirs = [
    'avatars', 'barangay_certificate', 'cedula', 'cenro_tickets',
    'driver_applications', 'driver_photos', 'educational',
    'educational_topics', 'mayors_permits', 'operator_docs'
]

for subdir in subdirs:
    subdir_path = os.path.join(settings.MEDIA_ROOT, subdir)
    os.makedirs(subdir_path, exist_ok=True)
    
    test_file = os.path.join(subdir_path, 'test_file.txt')
    with open(test_file, 'w') as f:
        f.write(f'Test file for {subdir}')
    
    print(f"{subdir} - /media/{subdir}/test_file.txt")
```

## Checking Logs

Check your application logs for any media-related errors:

1. Go to the Render dashboard
2. Select your web service
3. Click on "Logs"
4. Look for messages related to:
   - Media file requests
   - File not found errors
   - Permission issues

## After Fixing the Issue

After implementing the fixes:

1. **Restart your service** on Render
2. **Clear your browser cache**
3. **Check the logs** for any remaining errors
4. **Test file uploads and access** with different file types

If issues persist, check the Render documentation or contact Render support for specific filesystem limitations and recommendations.

## Manual Deployment Fix

If you need to apply fixes manually during deployment:

1. SSH into your Render instance
2. Navigate to your project directory
3. Run the fix script:
   ```bash
   python fix_render_media.py
   ```
4. Restart your service 