#!/usr/bin/env python3
"""
Script to check admin user status
"""

import os
import sys
from app import create_app, db
from app.models import Admin

def check_admin_user():
    """Check admin user status"""
    app = create_app()
    
    with app.app_context():
        # Check if admin exists
        admin = Admin.query.filter_by(email='admin@skillswap.com').first()
        
        if admin:
            print("✅ Admin user found!")
            print(f"ID: {admin.id}")
            print(f"Email: {admin.email}")
            print(f"Name: {admin.name}")
            print(f"Role: {admin.role}")
            print(f"Is Active: {admin.is_active}")
            print(f"Created: {admin.created_at}")
            print(f"Last Login: {admin.last_login}")
            
            # Test password
            if admin.check_password('admin123'):
                print("✅ Password check: PASSED")
            else:
                print("❌ Password check: FAILED")
                
        else:
            print("❌ Admin user not found!")
            print("Creating admin user...")
            
            # Create admin user
            admin = Admin(
                email='admin@skillswap.com',
                password='admin123',
                name='System Administrator',
                role='super_admin'
            )
            
            try:
                db.session.add(admin)
                db.session.commit()
                print("✅ Admin user created successfully!")
            except Exception as e:
                print(f"❌ Error creating admin user: {e}")
                db.session.rollback()

if __name__ == '__main__':
    check_admin_user() 