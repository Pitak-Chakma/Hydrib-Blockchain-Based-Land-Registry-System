from functools import wraps
from flask import session, redirect, url_for, flash, request, abort
import re
import os
from werkzeug.utils import secure_filename

def login_required(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(required_role):
    """Decorator to require specific role for protected routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please login to access this page', 'error')
                return redirect(url_for('login'))
            
            user_role = session.get('user_role')
            if user_role != required_role and user_role != 'admin':
                flash('You do not have permission to access this page', 'error')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_input(data, field_type='text', max_length=None, required=True):
    """Validate and sanitize input data"""
    if not data and required:
        return False, "This field is required"
    
    if not data:
        return True, data
    
    # Remove leading/trailing whitespace
    data = data.strip()
    
    # Check length
    if max_length and len(data) > max_length:
        return False, f"Maximum length is {max_length} characters"
    
    # Validate based on field type
    if field_type == 'email':
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data):
            return False, "Invalid email format"
    
    elif field_type == 'phone':
        # Bangladesh phone number pattern
        phone_pattern = r'^(\+88)?01[3-9]\d{8}$'
        if not re.match(phone_pattern, data):
            return False, "Invalid phone number format"
    
    elif field_type == 'numeric':
        try:
            float(data)
        except ValueError:
            return False, "Must be a valid number"
    
    elif field_type == 'plot_number':
        # Plot number should be alphanumeric with hyphens/underscores
        if not re.match(r'^[A-Za-z0-9_-]+$', data):
            return False, "Plot number can only contain letters, numbers, hyphens, and underscores"
    
    # Check for potential XSS attempts
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>.*?</iframe>'
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, data, re.IGNORECASE):
            return False, "Invalid characters detected"
    
    return True, data

def validate_file(file, allowed_extensions=None, max_size=None):
    """Validate uploaded file"""
    if not file or file.filename == '':
        return False, "No file selected"
    
    # Check file extension
    if allowed_extensions:
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if file_ext not in allowed_extensions:
            return False, f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
    
    # Check file size
    if max_size:
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > max_size:
            return False, f"File size too large. Maximum size: {max_size // (1024*1024)}MB"
    
    # Secure filename
    filename = secure_filename(file.filename)
    if not filename:
        return False, "Invalid filename"
    
    return True, filename

def sanitize_filename(filename):
    """Create a secure filename with timestamp"""
    import datetime
    
    # Get secure filename
    secure_name = secure_filename(filename)
    
    # Add timestamp to prevent conflicts
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    name, ext = os.path.splitext(secure_name)
    
    return f"{timestamp}_{name}{ext}"

def check_csrf_token():
    """Basic CSRF protection"""
    if request.method == 'POST':
        token = session.get('csrf_token')
        form_token = request.form.get('csrf_token')
        
        if not token or token != form_token:
            abort(403)

def generate_csrf_token():
    """Generate CSRF token for forms"""
    import secrets
    
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)
    
    return session['csrf_token']

def add_security_headers(response):
    """Add security headers to response"""
    security_headers = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }
    
    for header, value in security_headers.items():
        response.headers[header] = value
    
    return response

def rate_limit_check(identifier, limit=100, window=3600):
    """Simple rate limiting (in production, use Redis or similar)"""
    import time
    
    # This is a basic implementation - use proper rate limiting in production
    current_time = time.time()
    
    # In production, store this in Redis or database
    # For now, we'll use session-based limiting
    rate_limit_key = f"rate_limit_{identifier}"
    
    if rate_limit_key not in session:
        session[rate_limit_key] = []
    
    # Clean old entries
    session[rate_limit_key] = [
        timestamp for timestamp in session[rate_limit_key]
        if current_time - timestamp < window
    ]
    
    # Check if limit exceeded
    if len(session[rate_limit_key]) >= limit:
        return False
    
    # Add current request
    session[rate_limit_key].append(current_time)
    return True