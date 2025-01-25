from fastapi import FastAPI, Depends, HTTPException, status
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
from .agents.sentiment_analysis import SentimentAnalysisAgent

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

@app.post("/google-login", response_model=schemas.Token)
async def google_login(token: str, db: Session = Depends(database.get_db)):
    user_data = await oauth.verify_google_token(token)
    email = user_data.get("email")
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        user = models.User(
            email=email,
            auth_provider="google",
            role="user"  # Default role for Google login is 'user'
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    access_token = utils.create_access_token(data={"sub": email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me", response_model=schemas.User)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.get("/login-page")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

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

# Initialize sentiment analyzer
sentiment_analyzer = SentimentAnalysisAgent()

@app.post("/feedback", response_model=schemas.Feedback)
def create_feedback(
    feedback: schemas.FeedbackCreate,
    db: Session = Depends(database.get_db)
):
    # Analyze sentiment
    sentiment_result = sentiment_analyzer.analyze_sentiment(feedback.content)
    
    # Create feedback entry
    db_feedback = models.PublicFeedback(
        name=feedback.name,
        content=feedback.content,
        sentiment_score=sentiment_result["sentiment_score"],
        sentiment_label=sentiment_result["sentiment_label"],
        created_at=datetime.utcnow()
    )
    
    # Save to database
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    
    return db_feedback