from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, logout_user

main_bp = Blueprint('main', __name__)

@main_bp.before_app_request
def block_banned_users():
    if current_user.is_authenticated and hasattr(current_user, 'is_banned') and current_user.is_banned:
        logout_user()
        if request.endpoint != 'auth.login':
            flash('Your account has been banned. Please contact support.', 'error')
        return redirect(url_for('auth.login'))

@main_bp.route('/')
def index():
    """Homepage"""
    return render_template('index.html')

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@main_bp.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html') 