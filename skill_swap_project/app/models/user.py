from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from .. import db, login_manager

class User(UserMixin, db.Model):
    """User model for authentication and profile management"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(100))
    photo_url = db.Column(db.String(255))
    availability = db.Column(db.String(50), default='weekends')
    is_public = db.Column(db.Boolean, default=True)
    is_banned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    skills_offered = db.relationship('UserSkill', backref='user', lazy='dynamic', 
                                   foreign_keys='UserSkill.user_id')
    swap_requests_sent = db.relationship('SwapRequest', backref='requester', lazy='dynamic',
                                       foreign_keys='SwapRequest.requester_id')
    swap_requests_received = db.relationship('SwapRequest', backref='receiver', lazy='dynamic',
                                           foreign_keys='SwapRequest.receiver_id')
    feedback_given = db.relationship('Feedback', backref='rater', lazy='dynamic',
                                   foreign_keys='Feedback.rater_id')
    
    def __init__(self, name, email, password, location=None, photo_url=None, availability='weekends'):
        self.name = name
        self.email = email
        self.set_password(password)
        self.location = location
        self.photo_url = photo_url
        self.availability = availability
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert user to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'location': self.location,
            'photo_url': self.photo_url,
            'availability': self.availability,
            'is_public': self.is_public,
            'is_banned': self.is_banned,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def get_skills_offered(self):
        """Get list of skills offered by user"""
        return [skill.skill_name for skill in self.skills_offered.filter_by(skill_type='offered').all()]
    
    def get_skills_wanted(self):
        """Get list of skills wanted by user"""
        return [skill.skill_name for skill in self.skills_offered.filter_by(skill_type='wanted').all()]
    
    def is_available_for_swaps(self):
        """Check if user is available for new swap requests"""
        pending_requests = self.swap_requests_received.filter_by(status='pending').count()
        return pending_requests < 5  # Limit to 5 pending requests
    
    def __repr__(self):
        return f'<User {self.email}>'

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login (supports both User and Admin)"""
    from .admin import Admin
    user = User.query.get(int(user_id))
    if user:
        return user
    admin = Admin.query.get(int(user_id))
    return admin 