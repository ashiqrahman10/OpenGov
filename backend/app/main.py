from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Response, Body, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from . import models, schemas, database
from .auth import utils, oauth
from .database import engine
from .config import settings
from jose import JWTError
from datetime import datetime
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from .agents.groq_analyzer import GroqAnalyzer
from .services.firebase import FirebaseService
from typing import List, Optional
from .auth.oauth import get_current_user, get_current_user_optional
from .agents.file_agent import FileAgent
from .agents.report_analyzer import ReportAnalyzer
from fastapi import APIRouter
from .models import ReportStatus  # Add this import
from .agents.meeting_analyzer import MeetingAnalyzer
from PyPDF2 import PdfReader
import io

# Create all database tables
models.Base.metadata.drop_all(bind=engine)  # Drop existing tables
models.Base.metadata.create_all(bind=engine)  # Create new tables

app = FastAPI(
    title="OpenGov API",
    description="API for OpenGov applications",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "Login and registration operations"
        },
        {
            "name": "Users",
            "description": "User management operations"
        }
        # Add more tags as needed
    ]
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

templates = Jinja2Templates(directory="templates")

# Dependency
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = utils.jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

@app.post("/register", response_model=schemas.User, tags=["Authentication"])
async def register(
    user: schemas.UserCreate = Body(
        ...,
        description="User registration details",
        example={
            "email": "user@example.com",
            "password": "strongpassword123"
        }
    ),
    db: Session = Depends(database.get_db)
):
    """
    Register a new user.
    
    - **email**: Required. User's email address
    - **password**: Required. User's password (will be hashed)
    """
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = utils.get_password_hash(user.password)
    now = datetime.utcnow()
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        auth_provider="email",
        created_at=now,
        updated_at=now,
        role="user"  # Default role is 'user'
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# New endpoint to create admin users (protected)
@app.post("/create-admin", response_model=schemas.User, tags=["Users"])
async def create_admin(
    user: schemas.UserCreate = Body(
        ...,
        description="Admin user details",
        example={
            "email": "admin@example.com",
            "password": "adminpass123"
        }
    ),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """
    Create a new admin user.
    
    Requires authentication with admin privileges.
    
    - **email**: Required. Admin's email address
    - **password**: Required. Admin's password
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create other admin accounts"
        )
    
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = utils.get_password_hash(user.password)
    now = datetime.utcnow()
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        auth_provider="email",
        created_at=now,
        updated_at=now,
        role="admin"
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/token", response_model=schemas.Token, tags=["Authentication"])
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(database.get_db)
):
    """
    Login to get access token.
    
    - **username**: Required. User's email address
    - **password**: Required. User's password
    
    Returns an access token and token type.
    """
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not utils.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = utils.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/google-login")
async def google_login(
    token_data: dict,
    db: Session = Depends(database.get_db)
):
    try:
        result = await oauth.authenticate_google_user(token_data["token"], db)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.get("/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.get("/login-page")
async def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html", 
        {"request": request, "settings": settings}
    )

# Helper function to check admin status
def get_current_admin(current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only! In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Groq analyzer instead of sentiment analyzer
groq_analyzer = GroqAnalyzer(api_key=settings.GROQ_API_KEY)

# Initialize Firebase service
firebase_service = FirebaseService()

# Initialize FileAgent with both API keys
file_agent = FileAgent(
    groq_api_key=settings.GROQ_API_KEY,
    gemini_api_key=settings.GEMINI_API_KEY
)

# Initialize report analyzer
report_analyzer = ReportAnalyzer(
    groq_api_key=settings.GROQ_API_KEY,
    gemini_api_key=settings.GEMINI_API_KEY
)

# Create router
router = APIRouter(prefix="/reports", tags=["reports"])

@router.post("/", response_model=schemas.Report)
async def create_report(
    report: schemas.ReportCreate,
    db: Session = Depends(database.get_db)
):
    try:
        # Analyze report content
        analysis = await report_analyzer.analyze_report(report.content)
        
        # Check for sensitive information
        sensitive_info = await report_analyzer.detect_sensitive_info(report.content)
        
        # Assess credibility
        credibility = await report_analyzer.assess_credibility(report.content)
        
        # Generate unique report ID
        report_id = await report_analyzer.generate_report_id(analysis)
        
        # Create report record
        now = datetime.utcnow()
        db_report = models.Report(
            report_id=report_id,
            content=report.content,
            category=analysis["main_category"],
            sub_categories=analysis["sub_categories"],
            severity_level=analysis["severity_level"],
            priority_level=analysis["priority_level"],
            estimated_financial_impact=analysis.get("estimated_financial_impact"),
            entities_involved=analysis["entities_involved"],
            recommended_authorities=analysis["recommended_authorities"],
            risk_assessment=analysis["risk_assessment"],
            potential_evidence=analysis["potential_evidence"],
            summary=analysis["summary"],
            status=models.ReportStatus.SUBMITTED,
            credibility_score=credibility["credibility_score"],
            created_at=now,
            updated_at=now
        )
        
        db.add(db_report)
        db.commit()
        db.refresh(db_report)
        
        # Handle attachments if any
        if report.attachments:
            for attachment_url in report.attachments:
                db_attachment = models.ReportAttachment(
                    report_id=db_report.id,
                    file_url=attachment_url,
                    created_at=now
                )
                db.add(db_attachment)
            
            db.commit()
        
        return db_report
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing report: {str(e)}"
        )

@router.get("/{report_id}", response_model=schemas.Report)
async def get_report(
    report_id: str,
    db: Session = Depends(database.get_db)
):
    report = db.query(models.Report).filter(models.Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.post("/{report_id}/attachments")
async def add_attachment(
    report_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db)
):
    report = db.query(models.Report).filter(models.Report.report_id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    try:
        file_url = await firebase_service.upload_file(
            file,
            f"reports/{report_id}/attachments"
        )
        
        db_attachment = models.ReportAttachment(
            report_id=report.id,
            file_name=file.filename,
            file_type=file.content_type,
            file_url=file_url,
            created_at=datetime.utcnow()
        )
        
        db.add(db_attachment)
        db.commit()
        db.refresh(db_attachment)
        
        return {"message": "Attachment added successfully", "file_url": file_url}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading attachment: {str(e)}"
        )

@router.get("/{report_id}/investigation-steps")
async def get_investigation_steps(
    report_id: str,
    db: Session = Depends(database.get_db)
):
    try:
        # Get the report from database
        report = db.query(models.Report).filter(models.Report.report_id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
            
        # Generate investigation steps
        steps = await report_analyzer.generate_investigation_steps(report.content)
        
        if not steps:
            raise HTTPException(
                status_code=500, 
                detail="Failed to generate investigation steps"
            )
            
        return steps
    except Exception as e:
        print(f"Error in get_investigation_steps: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating investigation steps: {str(e)}"
        )

@router.post("/{report_id}/status")
async def update_report_status(
    report_id: str,
    status: ReportStatus = Body(...),
    notes: str = Body(...),
    db: Session = Depends(database.get_db)
):
    try:
        # Get the report
        report = db.query(models.Report).filter(models.Report.report_id == report_id).first()
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        
        # Update report status
        report.status = status
        
        # Create status update record
        update = models.ReportUpdate(
            report_id=report.id,
            status=status,
            notes=notes,
            created_at=datetime.utcnow()
        )
        
        db.add(update)
        db.commit()
        db.refresh(report)
        
        return {"message": "Status updated successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error updating report status: {str(e)}"
        )

@app.post("/feedback", response_model=schemas.Feedback)
def create_feedback(
    feedback: schemas.FeedbackCreate,
    db: Session = Depends(database.get_db)
):
    # Analyze feedback using Groq
    analysis = groq_analyzer.analyze_feedback(feedback.content)
    
    # Create feedback entry
    db_feedback = models.PublicFeedback(
        name=feedback.name,
        content=feedback.content,
        sentiment_score=analysis["sentiment_score"],
        sentiment_label=analysis["sentiment_label"],
        topics=",".join(analysis["topics"]),  # Convert list to comma-separated string
        summary=analysis["summary"],
        created_at=datetime.utcnow()
    )
    
    # Save to database
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    
    # Convert topics back to list for response
    return {
        **db_feedback.__dict__,
        "topics": db_feedback.topics.split(",") if db_feedback.topics else []
    }

@app.post("/documents/upload", response_model=schemas.Document)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth.get_current_user)
):
    try:
        # Upload file to Firebase with user_id
        user_id = current_user.id if current_user else None
        firebase_url = await firebase_service.upload_file(file, user_id)
        
        # Create document record in database
        db_document = models.Document(
            filename=file.filename,
            firebase_url=firebase_url,
            content_type=file.content_type,
            uploaded_by=user_id,
            created_at=datetime.utcnow()
        )
        
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        
        return db_document
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading document: {str(e)}"
        )

@app.get("/documents", response_model=List[schemas.Document])
def get_documents(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    try:
        documents = db.query(models.Document).filter(
            models.Document.uploaded_by == current_user.id
        ).all()
        return documents
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching documents: {str(e)}"
        )

@app.get("/documents/{document_id}", response_model=schemas.Document)
def get_document(
    document_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    document = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.uploaded_by == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document

@app.get("/upload-page")
async def upload_page(request: Request):
    return templates.TemplateResponse(
        "upload.html", 
        {"request": request}
    )

@app.get("/documents/{document_id}/content")
async def get_document_content(
    document_id: int,
    db: Session = Depends(database.get_db)
):
    # Get document without checking ownership
    document = db.query(models.Document).filter(
        models.Document.id == document_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        content, is_text = await file_agent.read_file_content(document.firebase_url, document.content_type)
        if is_text:
            return {"content": content}
        return Response(content=content, media_type=document.content_type)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading document content: {str(e)}"
        )

@app.get("/documents/{document_id}/summary", response_model=schemas.FileSummary)
async def get_document_summary(
    document_id: int,
    max_length: Optional[int] = 500,
    db: Session = Depends(database.get_db)
):
    # Get document without checking ownership
    document = db.query(models.Document).filter(
        models.Document.id == document_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        content, is_text = await file_agent.read_file_content(document.firebase_url, document.content_type)
        if not is_text:
            raise HTTPException(
                status_code=400,
                detail="Cannot summarize binary content. Only text files are supported."
            )
        summary = await file_agent.summarize_content(content, max_length)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error summarizing document: {str(e)}"
        )

@app.get("/documents/{document_id}/translate/{language}", response_model=schemas.FileTranslation)
async def translate_document(
    document_id: int,
    language: str,
    db: Session = Depends(database.get_db)
):
    # Get document without checking ownership
    document = db.query(models.Document).filter(
        models.Document.id == document_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        content, is_text = await file_agent.read_file_content(document.firebase_url, document.content_type)
        if not is_text:
            raise HTTPException(
                status_code=400,
                detail="Cannot translate binary content. Only text files are supported."
            )
        translated_content = await file_agent.translate_content(content, language)
        return {"translated_content": translated_content}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error translating document: {str(e)}"
        )

@app.post("/meetings/analyze", response_model=schemas.MeetingAnalysis)
async def analyze_meeting(
    file: UploadFile = File(...),
    title: str = Form(default="Untitled Meeting"),
    file_type: str = Form(default="audio"),  # 'audio' or 'pdf'
    db: Session = Depends(database.get_db)
):
    try:
        contents = await file.read()
        file_format = file.filename.split('.')[-1].lower()
        
        # Initialize analyzer
        analyzer = MeetingAnalyzer(
            groq_api_key=settings.GROQ_API_KEY,
            gemini_api_key=settings.GEMINI_API_KEY
        )
        
        # Handle different file types
        if file_type == "pdf":
            # Extract text from PDF
            pdf_file = io.BytesIO(contents)
            pdf_reader = PdfReader(pdf_file)
            transcript = ""
            for page in pdf_reader.pages:
                transcript += page.extract_text() + "\n"
        else:
            # Handle audio file
            transcript = await analyzer.transcribe_audio(contents, file_format)
        
        if not transcript:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to extract text from {file_type} file"
            )
        
        print(f"Text extraction successful. Length: {len(transcript)}")
        
        # Analyze the content
        analysis = await analyzer.analyze_meeting(transcript)
        
        # Store in database
        sentiment_map = {
            "positive": 1.0,
            "neutral": 0.0,
            "negative": -1.0
        }
        sentiment_score = sentiment_map.get(
            analysis["sentiment_analysis"].get("overall_tone", "neutral").lower(),
            0.0
        )
        
        # Create meeting record
        db_meeting = models.Meeting(
            title=title,
            date=datetime.utcnow(),
            file_path=f"meetings/{file.filename}",
            file_type=file_type,
            transcript=transcript,
            summary=analysis["summary"],
            sentiment_score=sentiment_score,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(db_meeting)
        db.commit()
        db.refresh(db_meeting)
        
        # Create topics
        for topic in analysis.get("key_topics", []):
            db_topic = models.MeetingTopic(
                meeting_id=db_meeting.id,
                topic=topic["topic"],
                key_points=topic["key_points"],
                decisions_made=topic.get("decisions_made", []),
                importance_level=topic.get("importance_level", "medium"),
                created_at=datetime.utcnow()
            )
            db.add(db_topic)
        
        # Create action items
        for item in analysis.get("action_items", []):
            db_action_item = models.ActionItem(
                meeting_id=db_meeting.id,
                description=item["task"],
                assigned_to=None,
                due_date=None,
                priority=item.get("priority", "medium"),
                status="pending",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(db_action_item)
        
        # Create participants
        for participant in analysis.get("participants", []):
            db_participant = models.MeetingParticipant(
                meeting_id=db_meeting.id,
                name=participant["name"],
                role=participant.get("role", "participant"),
                contributions=participant.get("contributions", []),
                created_at=datetime.utcnow()
            )
            db.add(db_participant)
        
        db.commit()
        
        return analysis
        
    except Exception as e:
        db.rollback()
        print(f"Error in analyze_meeting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing meeting: {str(e)}"
        )

@app.get("/meetings/{meeting_id}", response_model=schemas.Meeting)
async def get_meeting(
    meeting_id: int,
    db: Session = Depends(database.get_db)
):
    meeting = db.query(models.Meeting).filter(models.Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting

@app.get("/meetings/{meeting_id}/action-items", response_model=List[schemas.ActionItem])
async def get_meeting_action_items(
    meeting_id: int,
    db: Session = Depends(database.get_db)
):
    action_items = db.query(models.ActionItem).filter(
        models.ActionItem.meeting_id == meeting_id
    ).all()
    return action_items

@app.post("/meetings/{meeting_id}/action-items", response_model=schemas.ActionItem)
async def create_action_item(
    meeting_id: int,
    action_item: schemas.ActionItemCreate,
    db: Session = Depends(database.get_db)
):
    db_action_item = models.ActionItem(**action_item.dict(), meeting_id=meeting_id)
    db.add(db_action_item)
    db.commit()
    db.refresh(db_action_item)
    return db_action_item

@app.get("/meetings/{meeting_id}/minutes", response_model=schemas.MeetingMinutes)
async def get_meeting_minutes(
    meeting_id: int,
    db: Session = Depends(database.get_db)
):
    meeting = db.query(models.Meeting).filter(models.Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
        
    analyzer = MeetingAnalyzer(
        groq_api_key=settings.GROQ_API_KEY,
        gemini_api_key=settings.GEMINI_API_KEY,
        google_credentials_path=settings.GOOGLE_CREDENTIALS_PATH
    )
    
    # Convert SQLAlchemy objects to dictionaries
    analysis = {
        "summary": meeting.summary,
        "key_topics": [{
            "topic": topic.topic,
            "key_points": topic.key_points,
            "decisions_made": topic.decisions_made,
            "importance_level": topic.importance_level
        } for topic in meeting.topics],
        "action_items": [{
            "task": item.description,
            "assigned_to": item.assigned_to,
            "deadline": item.due_date,
            "priority": item.priority,
            "status": item.status
        } for item in meeting.action_items],
        "participants": [{
            "name": participant.name,
            "role": participant.role,
            "contributions": participant.contributions
        } for participant in meeting.participants]
    }
    
    minutes = await analyzer.generate_meeting_minutes(analysis)
    return {"content": minutes}

@app.put("/meetings/{meeting_id}/action-items/{item_id}", response_model=schemas.ActionItem)
async def update_action_item(
    meeting_id: int,
    item_id: int,
    action_item: schemas.ActionItemUpdate,
    db: Session = Depends(database.get_db)
):
    db_item = db.query(models.ActionItem).filter(
        models.ActionItem.id == item_id,
        models.ActionItem.meeting_id == meeting_id
    ).first()
    
    if not db_item:
        raise HTTPException(status_code=404, detail="Action item not found")
        
    for key, value in action_item.dict(exclude_unset=True).items():
        setattr(db_item, key, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item

@app.get("/users/{user_id}/action-items", response_model=List[schemas.ActionItem])
async def get_user_action_items(
    user_id: int,
    status: Optional[str] = None,
    db: Session = Depends(database.get_db)
):
    query = db.query(models.ActionItem).filter(models.ActionItem.assigned_to == user_id)
    if status:
        query = query.filter(models.ActionItem.status == status)
    return query.all()

# Add this line to include the router in the app
app.include_router(router)

@app.post("/upload", tags=["Files"])
async def upload_file(
    file: UploadFile = File(
        ...,
        description="File to upload (PDF, DOCX, etc.)"
    ),
    current_user: models.User = Depends(get_current_user)
):
    """
    Upload a file for processing.
    
    Requires authentication.
    
    Supported file types:
    - PDF
    - DOCX
    - Other supported formats
    """
    # Your existing code...