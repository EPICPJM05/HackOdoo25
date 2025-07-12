from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from .. import db

class Admin(UserMixin, db.Model):
    """Admin model for platform administration"""
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), default='admin')  # admin, super_admin
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def __init__(self, email, password, name, role='admin'):
        self.email = email
        self.set_password(password)
        self.name = name
        self.role = role
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert admin to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    @classmethod
    def create_default_admin(cls):
        """Create default admin user if none exists"""
        if cls.query.first() is None:
            admin = cls(
                email='admin@skillswap.com',
                password='admin123',
                name='System Administrator',
                role='super_admin'
            )
            db.session.add(admin)
            db.session.commit()
            return admin
        return None
    
    def __repr__(self):
        return f'<Admin {self.email}>' 

    def get_id(self):
        return f"admin-{self.id}" 