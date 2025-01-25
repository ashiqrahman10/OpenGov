from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Response
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

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

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

@app.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
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
@app.post("/create-admin", response_model=schemas.User)
def create_admin(
    user: schemas.UserCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
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

@app.post("/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
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