#!/usr/bin/env python3
"""
Script to create admin user for Skill Swap Platform
"""

import os
import sys
from app import create_app, db
from app.models import Admin

def create_admin_user():
    """Create admin user"""
    app = create_app()
    
    with app.app_context():
        # Check if admin already exists
        existing_admin = Admin.query.filter_by(email='admin@gmail.com').first()
        
        if existing_admin:
            print("✅ Admin user already exists!")
            print(f"Email: {existing_admin.email}")
            print("Password: admin123")
            return
        
        # Create new admin user
        admin = Admin(
            email='admin@gmail.com',
            password='admin123',
            name='System Administrator',
            role='super_admin'
        )
        
        try:
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created successfully!")
            print("Email: admin@skillswap.com")
            print("Password: admin123")
            print("\n⚠️  IMPORTANT: Change these credentials in production!")
        except Exception as e:
            print(f"❌ Error creating admin user: {e}")
            db.session.rollback()

if __name__ == '__main__':
    create_admin_user() 