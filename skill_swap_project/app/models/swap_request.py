from datetime import datetime
from .. import db

class SwapRequest(db.Model):
    """SwapRequest model for managing skill swap requests"""
    __tablename__ = 'swap_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    requester_skill = db.Column(db.String(100), nullable=False)  # Skill offered by requester
    receiver_skill = db.Column(db.String(100), nullable=False)   # Skill offered by receiver
    status = db.Column(db.Enum('pending', 'accepted', 'rejected', 'completed', 'cancelled'), 
                      default='pending')
    message = db.Column(db.Text)  # Optional message from requester
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def __init__(self, requester_id, receiver_id, requester_skill, receiver_skill, message=None):
        self.requester_id = requester_id
        self.receiver_id = receiver_id
        self.requester_skill = requester_skill
        self.receiver_skill = receiver_skill
        self.message = message
    
    def to_dict(self):
        """Convert swap request to dictionary"""
        return {
            'id': self.id,
            'requester_id': self.requester_id,
            'receiver_id': self.receiver_id,
            'requester_skill': self.requester_skill,
            'receiver_skill': self.receiver_skill,
            'status': self.status,
            'message': self.message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def accept(self):
        """Accept the swap request"""
        self.status = 'accepted'
        self.updated_at = datetime.utcnow()
    
    def reject(self):
        """Reject the swap request"""
        self.status = 'rejected'
        self.updated_at = datetime.utcnow()
    
    def complete(self):
        """Mark the swap as completed"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def cancel(self):
        """Cancel the swap request (only requester can do this)"""
        if self.status == 'pending':
            self.status = 'cancelled'
            self.updated_at = datetime.utcnow()
    
    @classmethod
    def get_user_requests(cls, user_id):
        """Get all swap requests for a user (sent and received)"""
        return cls.query.filter(
            (cls.requester_id == user_id) | (cls.receiver_id == user_id)
        ).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_pending_requests(cls, user_id):
        """Get pending swap requests for a user"""
        return cls.query.filter_by(receiver_id=user_id, status='pending').all()
    
    @classmethod
    def get_active_swaps(cls, user_id):
        """Get active (accepted) swaps for a user"""
        return cls.query.filter(
            ((cls.requester_id == user_id) | (cls.receiver_id == user_id)) &
            (cls.status == 'accepted')
        ).all()
    
    @classmethod
    def get_completed_swaps(cls, user_id):
        """Get completed swaps for a user"""
        return cls.query.filter(
            ((cls.requester_id == user_id) | (cls.receiver_id == user_id)) &
            (cls.status == 'completed')
        ).all()
    
    def can_be_cancelled_by(self, user_id):
        """Check if user can cancel this swap request"""
        return (self.requester_id == user_id and self.status == 'pending')
    
    def can_be_responded_by(self, user_id):
        """Check if user can respond to this swap request"""
        return (self.receiver_id == user_id and self.status == 'pending')
    
    def __repr__(self):
        return f'<SwapRequest {self.requester_id}->{self.receiver_id}: {self.status}>' 