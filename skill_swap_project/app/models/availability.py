from datetime import datetime, time
from .. import db

class Availability(db.Model):
    """Availability model for managing user availability time slots"""
    __tablename__ = 'availability'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Composite unique constraint
    __table_args__ = (
        db.UniqueConstraint('user_id', 'day_of_week', 'start_time', 'end_time', name='unique_availability_slot'),
    )
    
    def __init__(self, user_id, day_of_week, start_time, end_time, is_available=True):
        self.user_id = user_id
        self.day_of_week = day_of_week
        self.start_time = start_time
        self.end_time = end_time
        self.is_available = is_available
    
    def to_dict(self):
        """Convert availability to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'day_of_week': self.day_of_week,
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M') if self.end_time else None,
            'is_available': self.is_available,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def get_user_availability(cls, user_id):
        """Get all availability slots for a user"""
        return cls.query.filter_by(user_id=user_id, is_available=True).order_by(cls.day_of_week, cls.start_time).all()
    
    @classmethod
    def get_availability_by_day(cls, user_id, day_of_week):
        """Get availability for a specific day"""
        return cls.query.filter_by(user_id=user_id, day_of_week=day_of_week, is_available=True).all()
    
    @classmethod
    def create_default_availability(cls, user_id):
        """Create default weekend availability for a user"""
        # Weekend availability (Saturday and Sunday)
        weekend_slots = [
            (5, time(9, 0), time(12, 0)),   # Saturday morning
            (5, time(14, 0), time(18, 0)),  # Saturday afternoon
            (6, time(9, 0), time(12, 0)),   # Sunday morning
            (6, time(14, 0), time(18, 0)),  # Sunday afternoon
        ]
        
        for day, start, end in weekend_slots:
            availability = cls(user_id=user_id, day_of_week=day, start_time=start, end_time=end)
            db.session.add(availability)
        
        db.session.commit()
    
    def get_day_name(self):
        """Get day name from day number"""
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return days[self.day_of_week] if 0 <= self.day_of_week <= 6 else 'Unknown'
    
    def __repr__(self):
        return f'<Availability {self.user_id}: {self.get_day_name()} {self.start_time}-{self.end_time}>' 