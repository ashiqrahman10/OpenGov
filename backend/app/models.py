from sqlalchemy import Boolean, Column, Integer, String, DateTime, Enum, Text, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    auth_provider = Column(String, default="email")  # "email" or "google"
    role = Column(String, default="user")  # New field for user role
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Add relationships
    assigned_reports = relationship("Report", back_populates="assigned_user")
    action_items = relationship("ActionItem", back_populates="assigned_user")
    feedback = relationship("PublicFeedback", back_populates="user")
    documents = relationship("Document", back_populates="user")

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

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    category = Column(String)  # corruption, misuse_of_funds, unethical_practices
    severity_level = Column(String)  # high, medium, low
    status = Column(String, default="pending")  # pending, investigating, resolved
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    assigned_user = relationship("User", back_populates="assigned_reports")

class Meeting(Base):
    __tablename__ = "meetings"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    audio_file_path = Column(String)
    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Add relationship
    action_items = relationship("ActionItem", back_populates="meeting")

class ActionItem(Base):
    __tablename__ = "action_items"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"))
    description = Column(Text)
    assigned_to = Column(Integer, ForeignKey("users.id"))
    due_date = Column(DateTime, nullable=True)
    status = Column(String, default="pending")  # pending, in_progress, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    meeting = relationship("Meeting", back_populates="action_items")
    assigned_user = relationship("User", back_populates="action_items")