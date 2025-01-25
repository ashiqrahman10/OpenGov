from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

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

class ReportCreate(ReportBase):
    pass

class Report(ReportBase):
    id: int
    category: str
    severity_level: str
    status: str
    assigned_to: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MeetingBase(BaseModel):
    title: str
    date: datetime

class MeetingCreate(MeetingBase):
    audio_file_path: str

class Meeting(MeetingBase):
    id: int
    transcript: Optional[str] = None
    summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ActionItemBase(BaseModel):
    description: str
    assigned_to: int
    due_date: Optional[datetime] = None

class ActionItemCreate(ActionItemBase):
    meeting_id: int

class ActionItem(ActionItemBase):
    id: int
    meeting_id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True