from datetime import datetime
from .. import db

class Feedback(db.Model):
    """Feedback model for ratings and comments after swaps"""
    __tablename__ = 'feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    swap_id = db.Column(db.Integer, db.ForeignKey('swap_requests.id'), nullable=False)
    rater_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rated_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure rating is between 1 and 5
    __table_args__ = (
        db.CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
    )
    
    def __init__(self, swap_id, rater_id, rated_user_id, rating, comment=None):
        self.swap_id = swap_id
        self.rater_id = rater_id
        self.rated_user_id = rated_user_id
        self.rating = rating
        self.comment = comment
    
    def to_dict(self):
        """Convert feedback to dictionary"""
        return {
            'id': self.id,
            'swap_id': self.swap_id,
            'rater_id': self.rater_id,
            'rated_user_id': self.rated_user_id,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def get_user_feedback(cls, user_id):
        """Get all feedback for a user"""
        return cls.query.filter_by(rated_user_id=user_id).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_user_average_rating(cls, user_id):
        """Get average rating for a user"""
        result = cls.query.with_entities(db.func.avg(cls.rating)).filter_by(rated_user_id=user_id).scalar()
        return round(result, 1) if result else 0
    
    @classmethod
    def get_user_rating_count(cls, user_id):
        """Get number of ratings for a user"""
        return cls.query.filter_by(rated_user_id=user_id).count()
    
    @classmethod
    def get_swap_feedback(cls, swap_id):
        """Get all feedback for a specific swap"""
        return cls.query.filter_by(swap_id=swap_id).all()
    
    @classmethod
    def can_user_rate_swap(cls, user_id, swap_id):
        """Check if user can rate a specific swap"""
        # User can only rate if they participated in the swap and it's completed
        from .swap_request import SwapRequest
        swap = SwapRequest.query.get(swap_id)
        if not swap or swap.status != 'completed':
            return False
        
        # Check if user participated in the swap
        if swap.requester_id != user_id and swap.receiver_id != user_id:
            return False
        
        # Check if user already rated this swap
        existing_feedback = cls.query.filter_by(
            swap_id=swap_id, 
            rater_id=user_id
        ).first()
        
        return existing_feedback is None
    
    def __repr__(self):
        return f'<Feedback {self.rater_id}->{self.rated_user_id}: {self.rating} stars>' 