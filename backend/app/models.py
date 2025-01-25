from sqlalchemy import Boolean, Column, Integer, String, DateTime, Enum, Text, ForeignKey, Float, JSON, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
import enum

# Association table for User-Report many-to-many relationship
user_reports = Table(
    'user_reports',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('report_id', Integer, ForeignKey('reports.id'), primary_key=True),
    Column('assigned_at', DateTime, default=datetime.utcnow)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    auth_provider = Column(String, default="email")  # "email" or "google"
    role = Column(String, default="user")  # New field for user role
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    action_items = relationship("ActionItem", back_populates="assigned_user")
    feedback = relationship("PublicFeedback", back_populates="user")
    documents = relationship("Document", back_populates="user")
    reports = relationship("Report", secondary=user_reports, back_populates="assigned_users")

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    firebase_url = Column(String)
    content_type = Column(String)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="documents")

class PublicFeedback(Base):
    __tablename__ = "public_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    content = Column(Text)
    sentiment_score = Column(Float)
    sentiment_label = Column(String)  # positive, negative, neutral
    topics = Column(String)  # Stored as comma-separated string
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    user = relationship("User", back_populates="feedback")

class ReportStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    INVESTIGATING = "investigating"
    ESCALATED = "escalated"
    CLOSED = "closed"
    ARCHIVED = "archived"

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String, unique=True, index=True)  # Generated anonymous ID
    content = Column(Text)
    category = Column(String)
    sub_categories = Column(JSON)
    severity_level = Column(Integer)
    priority_level = Column(String)
    estimated_financial_impact = Column(Float, nullable=True)
    entities_involved = Column(JSON)  # Anonymized entities
    recommended_authorities = Column(JSON)
    risk_assessment = Column(Text)
    potential_evidence = Column(JSON)
    summary = Column(Text)
    status = Column(Enum(ReportStatus), default=ReportStatus.SUBMITTED)
    credibility_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    updates = relationship("ReportUpdate", back_populates="report")
    attachments = relationship("ReportAttachment", back_populates="report")
    assigned_users = relationship("User", secondary=user_reports, back_populates="reports")

class ReportUpdate(Base):
    __tablename__ = "report_updates"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"))
    status = Column(Enum(ReportStatus))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    report = relationship("Report", back_populates="updates")

class ReportAttachment(Base):
    __tablename__ = "report_attachments"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"))
    file_name = Column(String)
    file_type = Column(String)
    file_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    report = relationship("Report", back_populates="attachments")

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    date = Column(DateTime, default=datetime.utcnow)
    file_path = Column(String)  # Changed from audio_file_path
    file_type = Column(String)  # Added to distinguish between audio and PDF
    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    action_items = relationship("ActionItem", back_populates="meeting")
    topics = relationship("MeetingTopic", back_populates="meeting")
    participants = relationship("MeetingParticipant", back_populates="meeting")

class ActionItem(Base):
    __tablename__ = "action_items"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    description = Column(Text)
    assigned_to = Column(Integer, ForeignKey("users.id"))
    due_date = Column(DateTime, nullable=True)
    priority = Column(String)  # high, medium, low
    status = Column(String, default="pending")  # pending, in_progress, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    meeting = relationship("Meeting", back_populates="action_items")
    assigned_user = relationship("User", back_populates="action_items")

class MeetingTopic(Base):
    __tablename__ = "meeting_topics"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    topic = Column(String)
    key_points = Column(JSON)
    decisions_made = Column(JSON)
    importance_level = Column(String)  # high, medium, low
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    meeting = relationship("Meeting", back_populates="topics")

class MeetingParticipant(Base):
    __tablename__ = "meeting_participants"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String)
    role = Column(String)
    contributions = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    meeting = relationship("Meeting", back_populates="participants")
    user = relationship("User", backref="meeting_participations")