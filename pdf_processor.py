import os
import tempfile
import fitz  # PyMuPDF
import google.generativeai as genai
import json
import uuid
import datetime
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from models import Paper, Newsletter, UserUpload, User, Research
from database import SessionLocal
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyAsH6fY-voLT1WP4PgZL0b2nA3gZqoz6WQ"
genai.configure(api_key=GEMINI_API_KEY)

# Initialize Gemini model
model = genai.GenerativeModel('gemini-2.0-flash')

async def extract_text_from_pdf(file: UploadFile) -> str:
    """Extract text content from a PDF file."""
    try:
        # Create a temporary file to store the uploaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            # Write the uploaded file content to the temporary file
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        # Extract text from the PDF using PyMuPDF
        text_content = ""
        try:
            doc = fitz.open(temp_file_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text_content += page.get_text()
            doc.close()
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)

        return text_content
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to extract text from PDF: {str(e)}")

async def analyze_paper_with_gemini(text_content: str):
    """Use Gemini to analyze the paper content and extract structured information."""
    try:
        # Prompt engineering for structured extraction
        prompt = f"""
        You are a research paper analyzer. I'll provide the text content of a research paper, and I need you to extract the following information in a structured JSON format:

        1. Title of the paper
        2. Authors (as a list)
        3. DOI (Digital Object Identifier)
        4. Publication date
        5. Journal or conference name (source)
        6. Abstract
        7. Keywords (as a list)
        8. A comprehensive summary of the paper (around 500 words) as if you are explaining it to a non technical person. Format this using proper markdown with paragraphs, bullet points, and emphasis where appropriate.
        9. Main findings and contributions. Format this as a bulleted list using markdown.
        10. Methodology used in the research. Format this using proper markdown with sections, bullet points, and emphasis where appropriate.

        Here's the paper content:
        {text_content[:150000]}  # Limiting to first 150000 chars to avoid token limits

        If the paper is longer, focus on extracting information from the title, abstract, introduction, and conclusion sections.

        IMPORTANT INSTRUCTIONS FOR DOI EXTRACTION:
        - Look carefully for the DOI which is usually in the format 10.XXXX/XXXXX or https://doi.org/10.XXXX/XXXXX
        - DOIs are typically found in the header, footer, or first page of the paper
        - If you can't find a DOI, set the value to "not available" - do NOT make up a DOI
        - Check for patterns like "DOI:" or "https://doi.org/" in the text

        Return ONLY a JSON object with these fields, nothing else:
        {{
            "title": "Paper title",
            "authors": ["Author 1", "Author 2", ...],
            "doi": "DOI string if available, otherwise 'not available'",
            "publication_date": "YYYY-MM-DD or as specific as possible",
            "source": "Journal or conference name",
            "abstract": "The paper's abstract",
            "keywords": ["keyword1", "keyword2", ...],
            "summary": "Comprehensive summary",
            "main_findings": "Key findings and contributions",
            "methodology": "Research methodology used in the paper"
        }}
        """

        # Generate response from Gemini
        response = model.generate_content(prompt)

        # Extract and parse the JSON response
        try:
            # The response might be in markdown code blocks, so we need to clean it
            response_text = response.text
            if "```json" in response_text:
                # Extract JSON from markdown code block
                import re
                json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(1)
            elif "```" in response_text:
                # Extract JSON from generic code block
                import re
                json_match = re.search(r'```\n(.*?)\n```', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(1)

            import json
            paper_data = json.loads(response_text)
            return paper_data
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {str(e)}")
            logger.error(f"Raw response: {response.text}")
            raise HTTPException(status_code=500, detail=f"Failed to parse Gemini response: {str(e)}")

    except Exception as e:
        logger.error(f"Error analyzing paper with Gemini: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze paper with Gemini: {str(e)}")

async def store_paper_in_database(paper_data, user_id, original_pdf_path=None):
    """Store the extracted paper information in the database."""
    db = SessionLocal()
    try:
        # Handle DOI extraction
        # Check if DOI is missing or looks like a generated/invalid one
        if not paper_data.get("doi") or paper_data.get("doi").lower() in ["n/a", "none", "unknown", "not available"] or len(paper_data.get("doi", "")) < 5:
            # Create a DOI from the paper title in lowercase separated by hyphens
            # Remove special characters and replace spaces with hyphens
            import re
            title_slug = re.sub(r'[^\w\s-]', '', paper_data["title"].lower())
            title_slug = re.sub(r'[\s]+', '-', title_slug)

            # Use the title slug as the DOI
            paper_data["doi"] = title_slug

        # Check if paper with this DOI already exists
        existing_paper = db.query(Paper).filter(Paper.doi == paper_data["doi"]).first()

        # If paper exists, just create a user upload record
        if existing_paper:
            # Check if this user already uploaded this paper
            existing_upload = db.query(UserUpload).filter(
                UserUpload.user_id == user_id,
                UserUpload.doi == paper_data["doi"]
            ).first()

            if existing_upload:
                return {
                    "message": "You have already uploaded this paper",
                    "paper_doi": existing_paper.doi,
                    "redirect_url": f"/paper/{existing_paper.doi}"
                }

            # Create a new user upload record
            new_upload = UserUpload(
                user_id=user_id,
                doi=paper_data["doi"],
                original_pdf=original_pdf_path,
                summary=paper_data.get("summary", "")
            )
            db.add(new_upload)
            db.commit()

            return {
                "message": "Paper already exists in database, but added to your uploads",
                "paper_doi": existing_paper.doi,
                "upload_id": new_upload.upload_id,
                "redirect_url": f"/paper/{existing_paper.doi}"
            }

        # Create new Paper entry
        new_paper = Paper(
            doi=paper_data["doi"],
            title=paper_data["title"],
            authors=", ".join(paper_data["authors"]),
            source=paper_data.get("source", "Unknown"),
            data=json.dumps(paper_data),  # Store the full extracted data
            summary=paper_data.get("summary", "")
        )
        db.add(new_paper)

        # Create user upload record
        new_upload = UserUpload(
            user_id=user_id,
            doi=paper_data["doi"],
            original_pdf=original_pdf_path,
            summary=paper_data.get("summary", "")
        )
        db.add(new_upload)

        # Create Newsletter entry with the summary (for backward compatibility)
        new_newsletter = Newsletter(
            title=paper_data["title"],
            picture="/images/default_paper.jpg",  # Default image
            description=paper_data.get("abstract", "")[:200] + "...",  # Short description from abstract
            content=f"""# {paper_data["title"]}

## Authors
{", ".join(paper_data["authors"])}

## Abstract
{paper_data.get("abstract", "")}

## Summary
{paper_data.get("summary", "")}

## Main Findings
{paper_data.get("main_findings", "")}
"""
        )
        db.add(new_newsletter)

        # Also keep the Research entry for backward compatibility
        new_research = Research(
            title=paper_data["title"],
            authors=", ".join(paper_data["authors"]),
            doi=paper_data.get("doi", ""),
            publication_date=paper_data.get("publication_date", ""),
            venue=paper_data.get("source", ""),
            abstract=paper_data.get("abstract", ""),
            keywords=", ".join(paper_data.get("keywords", [])),
            methodology=""
        )
        db.add(new_research)

        db.commit()

        return {
            "message": "Paper successfully processed and stored",
            "paper_doi": new_paper.doi,
            "upload_id": new_upload.upload_id,
            "newsletter_id": new_newsletter.summary_id,  # For backward compatibility
            "redirect_url": f"/paper/{new_paper.doi}"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error storing paper in database: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to store paper in database: {str(e)}")
    finally:
        db.close()

async def process_pdf(file: UploadFile, user_id: int):
    """Process an uploaded PDF file: extract text, analyze with Gemini, and store in database.

    Args:
        file: The uploaded PDF file
        user_id: The ID of the user who uploaded the file

    Returns:
        A dictionary with information about the processed paper
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    # Create a path for storing the original PDF (optional)
    original_pdf_path = f"uploads/{uuid.uuid4()}_{file.filename}"

    # Extract text from PDF
    text_content = await extract_text_from_pdf(file)

    # Analyze paper with Gemini
    paper_data = await analyze_paper_with_gemini(text_content)

    # Store in database
    result = await store_paper_in_database(paper_data, user_id, original_pdf_path)

    return result
