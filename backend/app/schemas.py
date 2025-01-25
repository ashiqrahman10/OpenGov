from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List, Dict, Any
from .models import ReportStatus

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    auth_provider: str
    role: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None

class DocumentBase(BaseModel):
    filename: str

class DocumentCreate(DocumentBase):
    pass

class Document(BaseModel):
    id: int
    filename: str
    firebase_url: str
    content_type: str
    uploaded_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class FeedbackBase(BaseModel):
    content: str

class FeedbackCreate(BaseModel):
    name: str
    content: str

class Feedback(BaseModel):
    id: int
    name: str
    content: str
    sentiment_score: float
    sentiment_label: str
    topics: list[str]
    summary: str
    created_at: datetime

    class Config:
        from_attributes = True

class ReportBase(BaseModel):
    title: str
    description: str

class ReportCreate(BaseModel):
    content: str
    attachments: Optional[List[str]] = None

class ReportAttachmentBase(BaseModel):
    file_name: str
    file_type: str
    file_url: str
    created_at: datetime

class ReportUpdateBase(BaseModel):
    status: ReportStatus
    notes: str

class Report(BaseModel):
    id: int
    report_id: str
    content: str
    category: str
    sub_categories: List[str]
    severity_level: int
    priority_level: str
    estimated_financial_impact: Optional[float]
    entities_involved: List[Dict[str, str]]
    recommended_authorities: List[str]
    risk_assessment: str
    potential_evidence: List[str]
    summary: str
    status: ReportStatus
    credibility_score: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ReportAnalysis(BaseModel):
    main_category: str
    sub_categories: List[str]
    severity_level: int
    entities_involved: List[Dict[str, str]]
    estimated_financial_impact: Optional[float]
    recommended_authorities: List[str]
    risk_assessment: str
    priority_level: str
    potential_evidence: List[str]
    summary: str

class ReportCredibility(BaseModel):
    level_of_detail: int
    internal_consistency: int
    specificity: int
    verifiable_elements: List[str]
    potential_biases: List[str]
    completeness: int
    credibility_score: float
    confidence_level: float
    missing_information: List[str]
    recommendations: List[str]

class SensitiveInfo(BaseModel):
    names: List[str]
    contact_info: List[str]
    locations: List[str]
    financial_details: List[str]
    personal_ids: List[str]

# Base classes first
class MeetingBase(BaseModel):
    title: str
    date: datetime

class ActionItemBase(BaseModel):
    description: str
    assigned_to: int
    due_date: Optional[datetime] = None

class MeetingParticipantBase(BaseModel):
    name: str
    role: str
    contributions: List[str]

class MeetingTopicBase(BaseModel):
    topic: str
    key_points: List[str]
    decisions_made: List[str]
    importance_level: str

# Create/Update models
class MeetingCreate(MeetingBase):
    audio_file_path: str

class ActionItemCreate(ActionItemBase):
    priority: str = "medium"
    status: str = "pending"

class ActionItemUpdate(BaseModel):
    description: Optional[str] = None
    assigned_to: Optional[int] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None
    status: Optional[str] = None

# Full models with relationships
class ActionItem(ActionItemCreate):
    id: int
    meeting_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MeetingParticipant(MeetingParticipantBase):
    id: int

    class Config:
        from_attributes = True

class MeetingTopic(MeetingTopicBase):
    id: int

    class Config:
        from_attributes = True

class Meeting(MeetingBase):
    id: int
    summary: Optional[str] = None
    sentiment_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    action_items: List[ActionItem] = []
    topics: List[MeetingTopic] = []
    participants: List[MeetingParticipant] = []

    class Config:
        from_attributes = True

# Analysis models
class MeetingAnalysis(BaseModel):
    summary: str
    key_topics: List[Dict[str, Any]]
    action_items: List[Dict[str, Any]]
    participants: List[Dict[str, Any]]
    follow_up_needed: List[Dict[str, Any]]
    sentiment_analysis: Dict[str, Any]

class MeetingMinutes(BaseModel):
    content: str

class FileContent(BaseModel):
    content: str

class FileSummary(BaseModel):
    summary: str

class FileTranslation(BaseModel):
    translated_content: str