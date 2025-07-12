from datetime import datetime
from .. import db

class ChatMessage(db.Model):
    """ChatMessage model for swap-related conversations"""
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    swap_id = db.Column(db.Integer, db.ForeignKey('swap_requests.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='text')  # text, system
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sender = db.relationship('User', backref='sent_messages')
    swap = db.relationship('SwapRequest', backref='messages')
    
    def __init__(self, swap_id, sender_id, message, message_type='text'):
        self.swap_id = swap_id
        self.sender_id = sender_id
        self.message = message
        self.message_type = message_type
    
    def to_dict(self):
        """Convert message to dictionary for JSON response"""
        return {
            'id': self.id,
            'swap_id': self.swap_id,
            'sender_id': self.sender_id,
            'sender_name': self.sender.name if self.sender else 'System',
            'message': self.message,
            'message_type': self.message_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def get_swap_messages(cls, swap_id, limit=50):
        """Get messages for a specific swap"""
        return cls.query.filter_by(swap_id=swap_id)\
                       .order_by(cls.created_at.asc())\
                       .limit(limit)\
                       .all()
    
    @classmethod
    def create_system_message(cls, swap_id, message):
        """Create a system message for a swap"""
        return cls(
            swap_id=swap_id,
            sender_id=None,  # System messages don't have a sender
            message=message,
            message_type='system'
        )
    
    def __repr__(self):
        return f'<ChatMessage {self.sender_id}->{self.swap_id}: {self.message[:20]}...>' 