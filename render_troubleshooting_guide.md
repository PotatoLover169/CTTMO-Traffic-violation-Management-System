# Render Troubleshooting Guide: Fixing 500 Errors

This guide will help you identify and fix common causes of 500 errors when deploying your Django Traffic Violation System on Render.

## Quick Fixes for Common 500 Error Causes

### 1. Settings File Mismatch

The most common cause of 500 errors is a mismatch between the settings file specified in `render.yaml` and the one used in `wsgi.py`.

**Fixed in this commit:**
- Updated `wsgi.py` to use `CAPSTONE_PROJECT.postgresql_settings` when running on Render, matching the setting in `render.yaml`.
- Both files now consistently use the same settings module.

### 2. Check Your Render Logs

Always check your Render logs for specific error messages:

1. Log in to your Render dashboard
2. Select your web service (traffic-violation-system)
3. Click on the "Logs" tab
4. Look for Python error messages, particularly ImportError or ModuleNotFoundError

### 3. Database Configuration Issues

Database connection issues often cause 500 errors. Check:

- If your PostgreSQL database is active and properly connected
- Run `check_render_issues.py` to verify database connectivity
- Ensure `DATABASE_URL` environment variable is correctly set in Render dashboard

### 4. Media Directory Permissions

Media upload failures can cause 500 errors:

- Check if the `/opt/render/project/src/media` directory exists
- Ensure it has proper permissions (should be created by `build.sh`)
- Verify the disk configuration in `render.yaml` is correct

### 5. Missing Dependencies

ImportErrors for Python modules will cause 500 errors:

- Check if critical dependencies failed to install
- Run `check_render_issues.py` to detect missing dependencies
- Verify the `build.sh` script ran successfully during deployment

## Advanced Troubleshooting

### Manually Testing Your WSGI Application

SSH into your Render instance and run:

```bash
cd /opt/render/project/src
python -m gunicorn --check-config CAPSTONE_PROJECT.wsgi:application
```

### Checking Environment Variables

Verify all required environment variables are set:

```bash
python check_render_issues.py
```

### Testing PostgreSQL Connection

Test database connectivity:

```bash
cd /opt/render/project/src
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CAPSTONE_PROJECT.postgresql_settings')
django.setup()
from django.db import connections
connections['default'].ensure_connection()
print('Database connection successful')
"
```

## Deployment Checklist

Use this checklist to prevent common 500 errors:

1. ✅ Settings module in `wsgi.py` matches `render.yaml`
2. ✅ All required environment variables are set
3. ✅ Database URL is correctly configured
4. ✅ `build.sh` has proper permissions and runs successfully
5. ✅ `requirements.txt` or `requirements-fixed.txt` has all dependencies
6. ✅ Media directories are created with proper permissions
7. ✅ Static files are collected successfully

## Using the Check Script

Run the provided `check_render_issues.py` script locally or on Render to diagnose issues:

```bash
# Locally (with environment variables set)
python check_render_issues.py

# On Render via SSH or web terminal
cd /opt/render/project/src
python check_render_issues.py
```

## Common Error Messages and Solutions

### ImportError: No module named 'idanalyzer'

**Fix:** The idanalyzer module failed to install.
- Add `idanalyzer==1.2.2` to requirements-fixed.txt
- Ensure `handle_idanalyzer.py` is working correctly

### OperationalError: could not connect to server

**Fix:** Database connection issue.
- Verify the `DATABASE_URL` is correct
- Check if the PostgreSQL database is running
- Ensure your database plan is active

### PermissionError: [Errno 13] Permission denied: '/opt/render/project/src/media'

**Fix:** Media directory permission issue.
- Check if directory exists (`mkdir -p /opt/render/project/src/media`)
- Set permissions (`chmod -R 755 /opt/render/project/src/media`)

## Next Steps

If you're still experiencing 500 errors after following this guide:

1. Run `check_render_issues.py` to identify specific issues
2. Check Render logs for detailed Python error messages
3. Test individual Django views to isolate the problem
4. Consider temporarily enabling DEBUG=True (only briefly for diagnosis)
5. Contact Render support if infrastructure issues are suspected 