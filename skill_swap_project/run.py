#!/usr/bin/env python3
"""
Skill Swap Platform - Main Application Entry Point
"""

import os
from app import create_app, socketio
from app.models import Admin

# Create the application instance
app = create_app(os.getenv('FLASK_ENV', 'development'))

# Create default admin user if none exists
with app.app_context():
    Admin.create_default_admin()

if __name__ == '__main__':
    # Run the application
    socketio.run(app, 
                host='0.0.0.0', 
                port=int(os.environ.get('PORT', 5001)),
                debug=os.getenv('FLASK_ENV') == 'development') 