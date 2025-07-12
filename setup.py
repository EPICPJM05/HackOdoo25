#!/usr/bin/env python3
"""
Setup script for Skill Swap Platform
This script automates the initial setup process.
"""

import os
import sys
import subprocess
import mysql.connector
from mysql.connector import Error

def print_banner():
    """Print the setup banner"""
    print("=" * 60)
    print("🎉 Skill Swap Platform Setup")
    print("=" * 60)
    print()

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Error: Python 3.7 or higher is required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version.split()[0]}")

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "Back-End/requirements.txt"])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Error: Failed to install dependencies")
        sys.exit(1)

def setup_database():
    """Setup the MySQL database"""
    print("🗄️ Setting up database...")
    
    # Database configuration
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': ''
    }
    
    try:
        # Connect to MySQL server
        connection = mysql.connector.connect(**db_config)
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create database
            print("Creating database 'skill_swap'...")
            cursor.execute("CREATE DATABASE IF NOT EXISTS skill_swap")
            cursor.execute("USE skill_swap")
            
            # Create tables
            print("Creating tables...")
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    location VARCHAR(100),
                    photo_url VARCHAR(255),
                    availability VARCHAR(100),
                    is_public BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Skills offered table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS skills_offered (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    skill_name VARCHAR(100) NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Skills wanted table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS skills_wanted (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    skill_name VARCHAR(100) NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Swap requests table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS swap_requests (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    requester_id INT NOT NULL,
                    receiver_id INT NOT NULL,
                    status ENUM('pending', 'accepted', 'rejected', 'completed') DEFAULT 'pending',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (requester_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Feedback table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    swap_id INT NOT NULL,
                    rater_id INT NOT NULL,
                    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (swap_id) REFERENCES swap_requests(id) ON DELETE CASCADE,
                    FOREIGN KEY (rater_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
            
            # Admins table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert default admin user
            from werkzeug.security import generate_password_hash
            admin_password = generate_password_hash('admin123')
            cursor.execute("""
                INSERT IGNORE INTO admins (email, password) VALUES (%s, %s)
            """, ('admin@skillswap.com', admin_password))
            
            connection.commit()
            print("✅ Database setup completed successfully")
            
    except Error as e:
        print(f"❌ Database error: {e}")
        print("\nPlease ensure:")
        print("1. MySQL server is running")
        print("2. MySQL credentials are correct")
        print("3. You have permission to create databases")
        sys.exit(1)
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def create_upload_directory():
    """Create upload directory for profile photos"""
    upload_dir = "Back-End/static/uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        print(f"✅ Created upload directory: {upload_dir}")
    else:
        print(f"✅ Upload directory already exists: {upload_dir}")

def print_success():
    """Print success message"""
    print("\n" + "=" * 60)
    print("🎉 Setup completed successfully!")
    print("=" * 60)
    print("\n📋 Next steps:")
    print("1. Start the application:")
    print("   cd Back-End")
    print("   python app.py")
    print("\n2. Open your browser and go to: http://localhost:5000")
    print("\n3. Default admin account:")
    print("   Email: admin@skillswap.com")
    print("   Password: admin123")
    print("\n4. Register a new user account to start using the platform")
    print("\nHappy Skill Swapping! 🚀")

def main():
    """Main setup function"""
    print_banner()
    
    # Check Python version
    check_python_version()
    
    # Install dependencies
    install_dependencies()
    
    # Setup database
    setup_database()
    
    # Create upload directory
    create_upload_directory()
    
    # Print success message
    print_success()

if __name__ == "__main__":
    main() 