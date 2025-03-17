from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import List
from database import SessionLocal, engine
from models import Newsletter
from schemas import NewsletterBase

app = FastAPI()

# Mount static directories
app.mount("/static", StaticFiles(directory="pages"), name="static")  # CSS and JS from pages
app.mount("/images", StaticFiles(directory="images"), name="images")  # Images
app.mount("/videos", StaticFiles(directory="videos"), name="videos")  # Videos

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