from datetime import datetime
from .. import db

class UserSkill(db.Model):
    """UserSkill model for managing user skills (offered/wanted)"""
    __tablename__ = 'user_skills'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    skill_name = db.Column(db.String(100), nullable=False)  # For display, but relationship uses skill_id
    skill_type = db.Column(db.Enum('offered', 'wanted'), nullable=False)
    description = db.Column(db.Text)
    proficiency_level = db.Column(db.String(20), default='intermediate')  # beginner, intermediate, expert
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Composite unique constraint (user_id, skill_id, skill_type)
    __table_args__ = (
        db.UniqueConstraint('user_id', 'skill_id', 'skill_type', name='unique_user_skill_type'),
    )

    def __init__(self, user_id, skill_id, skill_name, skill_type, description=None, proficiency_level='intermediate'):
        self.user_id = user_id
        self.skill_id = skill_id
        self.skill_name = skill_name
        self.skill_type = skill_type
        self.description = description
        self.proficiency_level = proficiency_level

    def to_dict(self):
        """Convert user skill to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'skill_id': self.skill_id,
            'skill_name': self.skill_name,
            'skill_type': self.skill_type,
            'description': self.description,
            'proficiency_level': self.proficiency_level,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def get_user_offered_skills(cls, user_id):
        """Get all skills offered by a user"""
        return cls.query.filter_by(user_id=user_id, skill_type='offered').all()

    @classmethod
    def get_user_wanted_skills(cls, user_id):
        """Get all skills wanted by a user"""
        return cls.query.filter_by(user_id=user_id, skill_type='wanted').all()

    @classmethod
    def find_users_by_skill(cls, skill_id, skill_type='offered'):
        """Find users who offer or want a specific skill by skill_id"""
        return cls.query.filter_by(skill_id=skill_id, skill_type=skill_type).all()

    def __repr__(self):
        return f'<UserSkill {self.user_id}:{self.skill_name}({self.skill_type})>' 