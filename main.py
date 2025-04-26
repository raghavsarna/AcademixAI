from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta
import logging
import json
import os
import hashlib
import re

from database import SessionLocal, engine, create_tables
from models import Newsletter, User, Research, Paper, UserUpload
from schemas import NewsletterBase, UserCreate, UserResponse, Token, UserLogin
import auth
from auth import get_current_active_user, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
from pdf_processor import process_pdf
import google.generativeai as genai

app = FastAPI()

# Create database tables on startup
# This ensures the tables exist before any requests are processed
create_tables()

# Create a custom StaticFiles class with cache control headers
from fastapi.staticfiles import StaticFiles
from starlette.staticfiles import StaticFiles as StarletteStaticFiles
from starlette.responses import Response
from starlette.types import Scope, Receive, Send

class NoCacheStaticFiles(StarletteStaticFiles):
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async def send_with_no_cache_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"Cache-Control", b"no-cache, no-store, must-revalidate"))
                headers.append((b"Pragma", b"no-cache"))
                headers.append((b"Expires", b"0"))
                message["headers"] = headers
            await send(message)

        await super().__call__(scope, receive, send_with_no_cache_headers)

# Mount static directories with no-cache headers
app.mount("/static", NoCacheStaticFiles(directory="static"), name="static")  # CSS and JS files
app.mount("/images", NoCacheStaticFiles(directory="images"), name="images")  # Images
app.mount("/videos", NoCacheStaticFiles(directory="videos"), name="videos")  # Videos

# Mount pages directory for direct access to CSS files in pages
app.mount("/pages", NoCacheStaticFiles(directory="pages"), name="pages")

# Add routes to serve CSS files directly
from fastapi.responses import FileResponse

@app.get("/homepage.css")
async def get_homepage_css():
    return FileResponse("pages/homepage.css")

@app.get("/index.css")
async def get_index_css():
    response = FileResponse("pages/index.css")
    # Add cache control headers to prevent caching
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

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
    response = templates.TemplateResponse("index.html", {"request": request})
    # Add cache control headers to prevent caching
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/home", response_class=HTMLResponse)
async def read_home(request: Request):
    return templates.TemplateResponse("homepage.html", {"request": request})

@app.get("/content", response_class=HTMLResponse)
async def read_content(request: Request):
    return templates.TemplateResponse("content_page.html", {"request": request})

# API endpoints
@app.get("/api/papers", response_model=List[NewsletterBase])
async def get_papers(db: Session = Depends(get_db)):
    # Only return newsletters, not user-uploaded papers
    # This ensures user-uploaded papers are only visible in the user's profile
    papers = db.query(Newsletter).order_by(Newsletter.summary_id.desc()).all()
    return papers

@app.get("/api/latest-papers", response_model=List[NewsletterBase])
async def get_latest_papers(limit: int = 3, db: Session = Depends(get_db)):
    """
    Get the latest papers for display on the landing page.
    Returns the most recent newsletters, limited to the specified number (default: 3).
    """
    papers = db.query(Newsletter).order_by(Newsletter.summary_id.desc()).limit(limit).all()
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
async def chat_with_paper(summary_id: int, message: ChatMessage, db: Session = Depends(get_db)):
    # Get the newsletter from the database
    newsletter = db.query(Newsletter).filter(Newsletter.summary_id == summary_id).first()
    if newsletter is None:
        raise HTTPException(status_code=404, detail="Content not found")

    try:
        # Create context from newsletter information
        context = f"""Title: {newsletter.title}
        Description: {newsletter.description}
        Content: {newsletter.content}
        """

        # Create prompt for Gemini
        prompt = f"""You are an AI research assistant helping a user understand a research paper.
        Below is information about the paper. Use this context to answer the user's question.

        PAPER CONTEXT:
        {context}

        USER QUESTION: {message.message}

        Provide a clear, concise, and accurate answer based on the paper's content.
        If the answer cannot be determined from the paper, say so politely.
        """

        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-2.0-flash-lite')

        # Generate response
        response = model.generate_content(prompt)

        # Return the response
        return {"bot_message": response.text}
    except Exception as e:
        logging.error(f"Error generating chat response: {str(e)}")
        return {"bot_message": f"I'm sorry, I encountered an error while processing your question. Please try again."}

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyAsH6fY-voLT1WP4PgZL0b2nA3gZqoz6WQ"
genai.configure(api_key=GEMINI_API_KEY)

@app.post("/api/chat/paper/{doi}")
async def chat_with_paper_by_doi(doi: str, message: ChatMessage, db: Session = Depends(get_db)):
    # Get the paper from the database
    paper = db.query(Paper).filter(Paper.doi == doi).first()
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")

    try:
        # Extract paper data for context
        paper_data = {}
        if paper.data:
            try:
                paper_data = json.loads(paper.data)
            except:
                paper_data = {}

        # Create context from paper information
        context = f"""Title: {paper.title}
        Authors: {paper.authors}
        Source: {paper.source}
        Abstract: {paper_data.get('abstract', 'Not available')}
        Summary: {paper.summary}
        Main Findings: {paper_data.get('main_findings', 'Not available')}
        Methodology: {paper_data.get('methodology', 'Not available')}
        """

        # Create prompt for Gemini
        prompt = f"""You are an AI research assistant helping a user understand a research paper.
        Below is information about the paper. Use this context to answer the user's question.

        PAPER CONTEXT:
        {context}

        USER QUESTION: {message.message}

        Provide a clear, concise, and accurate answer based on the paper's content.
        If the answer cannot be determined from the paper, say so politely.
        """

        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-2.0-flash-lite')

        # Generate response
        response = model.generate_content(prompt)

        # Return the response
        return {"bot_message": response.text}
    except Exception as e:
        logging.error(f"Error generating chat response: {str(e)}")
        return {"bot_message": f"I'm sorry, I encountered an error while processing your question. Please try again."}

# Paper upload endpoint
from fastapi import File, UploadFile
from fastapi.responses import JSONResponse

@app.post("/api/upload")
async def upload_paper(file: UploadFile = File(...), current_user: User = Depends(get_current_active_user)):
    """Upload and process a research paper PDF.

    This endpoint:
    1. Extracts text from the uploaded PDF
    2. Uses Gemini to analyze the content
    3. Extracts metadata (DOI, title, authors, etc.)
    4. Generates a summary
    5. Stores the information in the database

    Returns a JSON response with the processing results and a redirect URL.
    """
    try:
        # Process the PDF using our processor module
        result = await process_pdf(file, current_user.id)
        return JSONResponse(content=result)
    except HTTPException as e:
        # Re-raise HTTP exceptions
        raise e
    except Exception as e:
        # Log and convert other exceptions to HTTP exceptions
        logging.error(f"Error processing PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

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

@app.get("/api/user/papers")
async def get_user_papers(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Get papers uploaded by the current authenticated user.
    These papers are only visible to the user who uploaded them and are not shown in the 'Latest Research' section.
    The 'Latest Research' section only shows newsletters from the Newsletter table.
    """
    # Get all papers uploaded by the current user
    user_uploads = db.query(UserUpload).filter(UserUpload.user_id == current_user.id).all()

    # Get the papers from the uploads
    papers = []
    for upload in user_uploads:
        paper = db.query(Paper).filter(Paper.doi == upload.doi).first()
        if paper:
            # Create a unique image filename based on the DOI
            image_filename = f"{hashlib.md5(paper.doi.encode()).hexdigest()}.jpg"
            image_path = f"/images/papers/{image_filename}"

            # Check if the image exists, otherwise use default
            if os.path.exists(os.path.join("images", "papers", image_filename)):
                image_url = image_path
            else:
                image_url = "/images/default_paper.jpg"

            # Extract paper data
            paper_data = {}
            if paper.data:
                try:
                    paper_data = json.loads(paper.data)
                except:
                    paper_data = {}

            # Add paper to the list
            papers.append({
                "doi": paper.doi,
                "title": paper.title,
                "authors": paper.authors,
                "source": paper.source,
                "summary": paper.summary,
                "image_url": image_url,
                "upload_date": upload.timestamp.isoformat() if upload.timestamp else None
            })

    # Sort papers by upload date (newest first)
    papers.sort(key=lambda x: x.get("upload_date", ""), reverse=True)

    return papers

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

# Upload page route
@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    return templates.TemplateResponse("upload_paper.html", {"request": request})

import requests
import os
import hashlib

# View paper route
@app.get("/paper/{doi}", response_class=HTMLResponse)
async def view_paper(request: Request, doi: str, db: Session = Depends(get_db)):
    # Get paper from database
    paper = db.query(Paper).filter(Paper.doi == doi).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    # Extract additional fields from the data JSON if available
    paper_data = {}
    if paper.data:
        try:
            import json
            paper_data = json.loads(paper.data)
        except:
            paper_data = {}

    # Handle the paper image
    image_url = ""
    # Create a unique image filename based on the DOI
    image_filename = f"{hashlib.md5(doi.encode()).hexdigest()}.jpg"
    image_path = os.path.join("images", "papers", image_filename)

    # Check if the image already exists
    if not os.path.exists(os.path.join("images", "papers")):
        os.makedirs(os.path.join("images", "papers"), exist_ok=True)

    if os.path.exists(image_path):
        # Use the existing image
        image_url = f"/images/papers/{image_filename}"
    else:
        try:
            # Download a new image from Lorem Picsum
            response = requests.get("https://picsum.photos/1200/400", stream=True)
            if response.status_code == 200:
                with open(image_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                image_url = f"/images/papers/{image_filename}"
            else:
                # Fallback to a default image
                image_url = "/images/default_paper.jpg"
        except Exception as e:
            logging.error(f"Error downloading image: {str(e)}")
            # Fallback to a default image
            image_url = "/images/default_paper.jpg"

    # Helper function to clean and format text for markdown
    def clean_text(text):
        if not text:
            return "No information available"

        # Fix common LLM formatting issues

        # 1. Fix asterisks for emphasis (bold/italic)
        # Replace multiple asterisks with proper markdown
        text = re.sub(r'\*\*\*([^*]+)\*\*\*', r'***\1***', text)  # Fix bold+italic
        text = re.sub(r'\*\*([^*]+)\*\*', r'**\1**', text)  # Fix bold
        text = re.sub(r'\*([^*]+)\*', r'*\1*', text)  # Fix italic

        # 2. Fix bullet points and lists
        # Ensure proper spacing for markdown lists
        text = re.sub(r'(\n\s*)-\s*', '\n- ', text)
        text = re.sub(r'(\n\s*)\*\s+', '\n* ', text)  # Alternative bullet style
        text = re.sub(r'(\n\s*)(\d+)\.\s+', '\n\1\2. ', text)  # Numbered lists

        # 3. Fix headers
        # Ensure proper spacing for markdown headers
        text = re.sub(r'(\n\s*)#\s+', '\n# ', text)
        text = re.sub(r'(\n\s*)##\s+', '\n## ', text)
        text = re.sub(r'(\n\s*)###\s+', '\n### ', text)

        # 4. Fix common formatting patterns from LLM output
        # Convert "Title:" patterns to headers
        text = re.sub(r'\n([A-Za-z\s]+):\s*\n', r'\n## \1\n', text)

        # 5. Fix quotes
        text = re.sub(r'(\n\s*)>\s*', '\n> ', text)

        # 6. Fix code blocks
        text = re.sub(r'```([^`]*)```', r'```\n\1\n```', text)

        # 7. Fix line breaks - ensure paragraphs have proper spacing
        text = re.sub(r'\n{3,}', '\n\n', text)  # Replace multiple line breaks with double

        # 8. Fix special characters that might break markdown
        text = text.replace('\\*', '*')
        text = text.replace('\\#', '#')
        text = text.replace('\\[', '[')
        text = text.replace('\\]', ']')

        # 9. Fix raw LLM formatting patterns
        # Convert "**Key Finding:**" patterns to proper markdown
        text = re.sub(r'\*\*([^:]+):\*\*\s*', r'**\1:** ', text)

        return text

    # Create a complete paper object with all fields
    complete_paper = {
        "doi": paper.doi,
        "title": paper.title,
        "authors": paper.authors,
        "source": paper.source,
        "summary": clean_text(paper.summary),
        "abstract": clean_text(paper_data.get("abstract", "No abstract available")),
        "main_findings": clean_text(paper_data.get("main_findings", "No main findings available")),
        "methodology": clean_text(paper_data.get("methodology", "No methodology information available")),
        "image_url": image_url
    }

    # Render the paper view template
    return templates.TemplateResponse("paper_view.html", {
        "request": request,
        "paper": complete_paper
    })