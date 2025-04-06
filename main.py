from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta

from database import SessionLocal, engine, create_tables
from models import Newsletter, User
from schemas import NewsletterBase, UserCreate, UserResponse, Token, UserLogin
import auth
from auth import get_current_active_user, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES

app = FastAPI()

# Create database tables on startup
# This ensures the tables exist before any requests are processed
create_tables()

# Mount static directories
app.mount("/static", StaticFiles(directory="pages"), name="static")  # CSS and JS from pages
app.mount("/images", StaticFiles(directory="images"), name="images")  # Images
app.mount("/videos", StaticFiles(directory="videos"), name="videos")  # Videos

# Add routes to serve CSS files directly
from fastapi.responses import FileResponse

@app.get("/homepage.css")
async def get_homepage_css():
    return FileResponse("pages/homepage.css")

@app.get("/index.css")
async def get_index_css():
    return FileResponse("pages/index.css")

@app.get("/content_page.css")
async def get_content_page_css():
    response = FileResponse("pages/content_page.css")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/login.css")
async def get_login_css():
    response = FileResponse("pages/login.css")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/profile.css")
async def get_profile_css():
    response = FileResponse("pages/profile.css")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Set up Jinja2 templates from pages directory
templates = Jinja2Templates(directory="pages")

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Routes for HTML pages
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/home", response_class=HTMLResponse)
async def read_home(request: Request):
    return templates.TemplateResponse("homepage.html", {"request": request})

@app.get("/content", response_class=HTMLResponse)
async def read_content(request: Request):
    return templates.TemplateResponse("content_page.html", {"request": request})

# API endpoints
@app.get("/api/papers", response_model=List[NewsletterBase])
async def get_papers(db: Session = Depends(get_db)):
    papers = db.query(Newsletter).order_by(Newsletter.summary_id.desc()).all()
    return papers

@app.get("/api/paper/{summary_id}", response_model=NewsletterBase)
async def get_paper(summary_id: int, db: Session = Depends(get_db)):
    paper = db.query(Newsletter).filter(Newsletter.summary_id == summary_id).first()
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper

# Placeholder for chat functionality
from pydantic import BaseModel

class ChatMessage(BaseModel):
    message: str

@app.post("/api/chat/{summary_id}")
async def chat_with_paper(summary_id: int, message: ChatMessage):
    # Placeholder: Echo the message (replace with AI logic later)
    return {"bot_message": f"You said: {message.message}"}

# Placeholder for paper upload
from fastapi import File, UploadFile

@app.post("/api/upload")
async def upload_paper(file: UploadFile = File(...)):
    # Placeholder: Add logic to process PDF
    return {"message": "Paper uploaded successfully"}

# Authentication endpoints
@app.post("/api/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if username already exists
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Check if email already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user
    hashed_password = auth.get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/api/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# Login page route
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Register page route
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# Profile page route
@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})