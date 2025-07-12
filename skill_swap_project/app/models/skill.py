from datetime import datetime
from .. import db

class Skill(db.Model):
    """Skill model for platform skills"""
    __tablename__ = 'skills'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), default='general')
    is_approved = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_skills = db.relationship('UserSkill', backref='skill', lazy='dynamic')
    
    def __init__(self, name, description=None, category='general', is_approved=True):
        self.name = name
        self.description = description
        self.category = category
        self.is_approved = is_approved
    
    def to_dict(self):
        """Convert skill to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'is_approved': self.is_approved,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_approved_skills(cls):
        """Get all approved skills"""
        return cls.query.filter_by(is_approved=True).order_by(cls.name).all()
    
    @classmethod
    def get_by_category(cls, category):
        """Get skills by category"""
        return cls.query.filter_by(category=category, is_approved=True).order_by(cls.name).all()
    
    @classmethod
    def search_skills(cls, search_term):
        """Search skills by name"""
        return cls.query.filter(
            cls.name.ilike(f'%{search_term}%'),
            cls.is_approved == True
        ).order_by(cls.name).all()
    
    def __repr__(self):
        return f'<Skill {self.name}>' 