from flask import Blueprint, render_template
from flask_login import current_user

main_bp = Blueprint('main', __name__)

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