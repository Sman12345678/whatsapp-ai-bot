from app import db
from datetime import datetime
from sqlalchemy import func

class User(db.Model):
    """User model for WhatsApp users"""
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_banned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    messages = db.relationship('Message', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.phone_number}>'

class Group(db.Model):
    """Group model for WhatsApp groups"""
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    messages = db.relationship('Message', backref='group', lazy=True)
    
    def __repr__(self):
        return f'<Group {self.name}>'

class Message(db.Model):
    """Message model for tracking messages"""
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)
    content = db.Column(db.Text, nullable=True)
    message_type = db.Column(db.String(50), nullable=False)  # text, image, document, etc.
    is_command = db.Column(db.Boolean, default=False)
    command_name = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Message {self.message_id}>'

class AIRequest(db.Model):
    """AI request tracking"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    request_type = db.Column(db.String(50), nullable=False)  # chat, image_analysis, file_analysis
    prompt = db.Column(db.Text, nullable=True)
    response = db.Column(db.Text, nullable=True)
    tokens_used = db.Column(db.Integer, default=0)
    processing_time = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='ai_requests')
    
    def __repr__(self):
        return f'<AIRequest {self.request_type}>'

class FileProcessing(db.Model):
    """File processing tracking"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    content_extracted = db.Column(db.Boolean, default=False)
    ai_analyzed = db.Column(db.Boolean, default=False)
    processing_time = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='file_processings')
    
    def __repr__(self):
        return f'<FileProcessing {self.filename}>'

class BotStats(db.Model):
    """Bot statistics tracking"""
    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(100), nullable=False)
    metric_value = db.Column(db.Integer, default=0)
    date = db.Column(db.Date, default=datetime.utcnow().date())
    
    def __repr__(self):
        return f'<BotStats {self.metric_name}: {self.metric_value}>'
