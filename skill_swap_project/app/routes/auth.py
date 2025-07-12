from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from ..models import User, Admin
from .. import db
import re

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    return True, ""

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('users.profile'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        location = request.form.get('location', '').strip()
        
        # Validation
        errors = []
        
        if not name:
            errors.append("Name is required")
        elif len(name) < 2:
            errors.append("Name must be at least 2 characters long")
        
        if not email:
            errors.append("Email is required")
        elif not validate_email(email):
            errors.append("Please enter a valid email address")
        elif User.query.filter_by(email=email).first():
            errors.append("Email already registered")
        
        if not password:
            errors.append("Password is required")
        else:
            is_valid, error_msg = validate_password(password)
            if not is_valid:
                errors.append(error_msg)
        
        if password != confirm_password:
            errors.append("Passwords do not match")
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html', 
                                name=name, email=email, location=location)
        
        # Create user
        try:
            user = User(
                name=name,
                email=email,
                password=password,
                location=location if location else None
            )
            db.session.add(user)
            db.session.commit()
            
            # Log in the user
            login_user(user)
            flash('Registration successful! Welcome to Skill Swap!', 'success')
            return redirect(url_for('users.profile'))
            
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            return render_template('auth/register.html', 
                                name=name, email=email, location=location)
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('users.profile'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        if not email or not password:
            flash('Please enter both email and password', 'error')
            return render_template('auth/login.html', email=email)
        
        # Regular user login only (admin login is handled separately)
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if user.is_banned:
                flash('Your account has been banned. Please contact support.', 'error')
                return render_template('auth/login.html', email=email)
            
            login_user(user, remember=remember)
            flash('Login successful!', 'success')
            
            # Redirect to intended page or profile
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('users.profile'))
        else:
            flash('Invalid email or password', 'error')
            return render_template('auth/login.html', email=email)
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login"""
    print(f"Admin login route accessed. Current user: {current_user}")
    print(f"Current user authenticated: {current_user.is_authenticated}")
    print(f"Current user has role: {hasattr(current_user, 'role') if current_user.is_authenticated else 'N/A'}")
    
    if current_user.is_authenticated:
        if hasattr(current_user, 'role'):  # Admin user
            print("Redirecting admin user to dashboard")
            return redirect(url_for('admin.dashboard'))
        else:  # Regular user
            print("Redirecting regular user to profile")
            return redirect(url_for('users.profile'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        print(f"Admin login attempt: {email}")  # Debug
        
        if not email or not password:
            flash('Please enter both email and password', 'error')
            return render_template('auth/admin_login.html', email=email)
        
        admin = Admin.query.filter_by(email=email, is_active=True).first()
        print(f"Admin found: {admin is not None}")  # Debug
        
        if admin and admin.check_password(password):
            print("Admin password check passed")  # Debug
            login_user(admin)
            admin.update_last_login()
            flash('Welcome back, Administrator!', 'success')
            print("Redirecting to admin dashboard")  # Debug
            return redirect(url_for('admin.dashboard'))
        else:
            print("Admin login failed")  # Debug
            flash('Invalid admin credentials', 'error')
            return render_template('auth/admin_login.html', email=email)
    
    print("Rendering admin login template")
    return render_template('auth/admin_login.html')

# API endpoints for AJAX requests
@auth_bp.route('/api/check-email', methods=['POST'])
def check_email():
    """Check if email is available for registration"""
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    
    if not email:
        return jsonify({'available': False, 'message': 'Email is required'})
    
    if not validate_email(email):
        return jsonify({'available': False, 'message': 'Invalid email format'})
    
    user_exists = User.query.filter_by(email=email).first() is not None
    admin_exists = Admin.query.filter_by(email=email).first() is not None
    
    if user_exists or admin_exists:
        return jsonify({'available': False, 'message': 'Email already registered'})
    
    return jsonify({'available': True, 'message': 'Email is available'})

@auth_bp.route('/api/validate-password', methods=['POST'])
def validate_password_api():
    """Validate password strength via API"""
    data = request.get_json()
    password = data.get('password', '')
    
    is_valid, message = validate_password(password)
    return jsonify({'valid': is_valid, 'message': message}) 