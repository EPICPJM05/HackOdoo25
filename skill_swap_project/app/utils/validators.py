import re
from datetime import datetime

def validate_email(email):
    """Validate email format"""
    if not email:
        return False, "Email is required"
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Please enter a valid email address"
    
    return True, ""

def validate_password(password):
    """Validate password strength"""
    if not password:
        return False, "Password is required"
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    
    if len(password) > 128:
        return False, "Password must be less than 128 characters"
    
    return True, ""

def validate_name(name):
    """Validate user name"""
    if not name:
        return False, "Name is required"
    
    if len(name) < 2:
        return False, "Name must be at least 2 characters long"
    
    if len(name) > 100:
        return False, "Name must be less than 100 characters"
    
    # Check for valid characters (letters, spaces, hyphens, apostrophes)
    if not re.match(r'^[a-zA-Z\s\'-]+$', name):
        return False, "Name can only contain letters, spaces, hyphens, and apostrophes"
    
    return True, ""

def validate_skill_name(skill_name):
    """Validate skill name"""
    if not skill_name:
        return False, "Skill name is required"
    
    if len(skill_name) < 2:
        return False, "Skill name must be at least 2 characters long"
    
    if len(skill_name) > 100:
        return False, "Skill name must be less than 100 characters"
    
    # Check for valid characters (letters, numbers, spaces, hyphens)
    if not re.match(r'^[a-zA-Z0-9\s\-]+$', skill_name):
        return False, "Skill name can only contain letters, numbers, spaces, and hyphens"
    
    return True, ""

def validate_rating(rating):
    """Validate rating (1-5 stars)"""
    try:
        rating_int = int(rating)
        if rating_int < 1 or rating_int > 5:
            return False, "Rating must be between 1 and 5"
        return True, ""
    except (ValueError, TypeError):
        return False, "Rating must be a number between 1 and 5"

def validate_location(location):
    """Validate location (optional)"""
    if not location:
        return True, ""  # Location is optional
    
    if len(location) > 100:
        return False, "Location must be less than 100 characters"
    
    return True, ""

def sanitize_text(text, max_length=1000):
    """Sanitize text input"""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    return text.strip()

def validate_availability(availability):
    """Validate availability setting"""
    valid_options = ['weekends', 'evenings', 'weekdays', 'flexible']
    if availability not in valid_options:
        return False, "Invalid availability option"
    
    return True, ""

def validate_skill_type(skill_type):
    """Validate skill type"""
    if skill_type not in ['offered', 'wanted']:
        return False, "Invalid skill type"
    
    return True, ""

def validate_proficiency_level(level):
    """Validate proficiency level"""
    valid_levels = ['beginner', 'intermediate', 'expert']
    if level not in valid_levels:
        return False, "Invalid proficiency level"
    
    return True, ""

def validate_swap_request_data(data):
    """Validate swap request data"""
    errors = []
    
    # Validate receiver_id
    if not data.get('receiver_id'):
        errors.append("Receiver ID is required")
    
    # Validate skills
    requester_skill = data.get('requester_skill', '').strip()
    receiver_skill = data.get('receiver_skill', '').strip()
    
    is_valid, error_msg = validate_skill_name(requester_skill)
    if not is_valid:
        errors.append(f"Requester skill: {error_msg}")
    
    is_valid, error_msg = validate_skill_name(receiver_skill)
    if not is_valid:
        errors.append(f"Receiver skill: {error_msg}")
    
    # Validate message (optional)
    message = data.get('message', '').strip()
    if message:
        message = sanitize_text(message, 500)
    
    return errors, {
        'requester_skill': requester_skill,
        'receiver_skill': receiver_skill,
        'message': message
    }

def validate_feedback_data(data):
    """Validate feedback data"""
    errors = []
    
    # Validate rating
    rating = data.get('rating')
    is_valid, error_msg = validate_rating(rating)
    if not is_valid:
        errors.append(error_msg)
    
    # Validate comment (optional)
    comment = data.get('comment', '').strip()
    if comment:
        comment = sanitize_text(comment, 500)
    
    return errors, {
        'rating': int(rating) if rating else None,
        'comment': comment
    }

def format_datetime(dt):
    """Format datetime for display"""
    if not dt:
        return ""
    
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            return dt
    
    return dt.strftime('%B %d, %Y at %I:%M %p')

def format_date(dt):
    """Format date for display"""
    if not dt:
        return ""
    
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            return dt
    
    return dt.strftime('%B %d, %Y')

def format_time(dt):
    """Format time for display"""
    if not dt:
        return ""
    
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            return dt
    
    return dt.strftime('%I:%M %p') 