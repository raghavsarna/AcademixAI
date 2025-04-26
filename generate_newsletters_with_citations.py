"""
Script to generate research newsletters with proper citations for April 20-26, 2025.
"""

import arxiv
import google.generativeai as genai
import datetime
import logging
import os
import requests
import hashlib
import time
from typing import List, Dict, Any
from database import SessionLocal
from models import Newsletter
from generate_weekly_newsletters import fetch_arxiv_papers_for_date, prepare_paper_data, summarize_with_gemini

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure Gemini API
genai.configure(api_key="AIzaSyAsH6fY-voLT1WP4PgZL0b2nA3gZqoz6WQ")

def save_to_database(title: str, content: str, description: str, date: datetime.datetime) -> int:
    """
    Save the generated content to the newsletter database.
    
    Args:
        title: The title of the newsletter
        content: The content of the newsletter
        description: A brief description of the newsletter
        date: The date of the newsletter
        
    Returns:
        The ID of the newly created newsletter entry
    """
    logger.info(f"Saving content to database for date {date.strftime('%Y-%m-%d')}...")
    
    try:
        # Create a database session
        db = SessionLocal()
        
        # Generate a unique filename for the image
        # Include date and a random number to ensure uniqueness
        random_suffix = str(int(time.time() * 1000) % 10000)  # Use current time milliseconds
        image_filename = f"{date.strftime('%Y%m%d')}_{random_suffix}_{hashlib.md5((title + random_suffix).encode()).hexdigest()}.jpg"
        image_path = os.path.join("images", "papers", image_filename)
        image_url = f"/images/papers/{image_filename}"
        
        # Ensure the directory exists
        os.makedirs(os.path.join("images", "papers"), exist_ok=True)
        
        # Check if the image already exists (to avoid re-downloading)
        if not os.path.exists(image_path):
            try:
                # Use completely random images from Lorem Picsum
                # Generate a unique random number for each image
                random_number = int(time.time() * 1000) % 1000000
                random_image_url = f"https://picsum.photos/seed/{random_number}/1200/400"
                
                # Download the image
                logger.info(f"Downloading random image with seed {random_number}")
                response = requests.get(random_image_url, stream=True)
                
                if response.status_code == 200:
                    with open(image_path, 'wb') as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                    logger.info("Successfully downloaded random image")
                else:
                    logger.error(f"Failed to download random image: HTTP {response.status_code}")
                    # Fall back to a random image
                    logger.info("Falling back to random Lorem Picsum image")
                    response = requests.get("https://picsum.photos/1200/400", stream=True)
                    
                    if response.status_code == 200:
                        with open(image_path, 'wb') as f:
                            for chunk in response.iter_content(1024):
                                f.write(chunk)
                        logger.info("Successfully downloaded random image")
                    else:
                        # Use a default image URL if all else fails
                        logger.error(f"Failed to download random image: HTTP {response.status_code}")
                        image_url = "/static/default_paper.jpg"
            except Exception as e:
                logger.error(f"Error downloading image: {str(e)}")
                # Use a default image URL
                image_url = "/static/default_paper.jpg"
        
        # Create a new newsletter entry
        new_newsletter = Newsletter(
            title=title,
            picture=image_url,
            content=content,
            description=description,
            date=date
        )
        
        # Add to database and commit
        db.add(new_newsletter)
        db.commit()
        db.refresh(new_newsletter)
        
        # Get the ID of the new entry
        summary_id = new_newsletter.summary_id
        
        # Close the database session
        db.close()
        
        logger.info(f"Successfully saved to database with ID: {summary_id}")
        return summary_id
        
    except Exception as e:
        logger.error(f"Error saving to database: {str(e)}")
        raise

def generate_newsletter_for_date(date: datetime.datetime):
    """
    Generate a newsletter for a specific date.
    
    Args:
        date: The date to generate the newsletter for
    """
    try:
        # Fetch papers from arXiv for the specific date
        papers = fetch_arxiv_papers_for_date(date)
        
        # If no papers were found, skip this date
        if not papers:
            logger.warning(f"No papers found for date {date.strftime('%Y-%m-%d')}, skipping...")
            return
        
        # Prepare paper data
        paper_data = prepare_paper_data(papers)
        
        logger.info(f"Processing {len(paper_data)} papers for {date.strftime('%Y-%m-%d')}'s digest")
        
        # Summarize papers with Gemini
        # Add the date to the prompt to ensure it uses the correct date
        formatted_date = date.strftime("%Y-%m-%d")
        custom_prompt = f"""Generate a newsletter for AI research papers published on {formatted_date}. 
        
IMPORTANT FORMATTING INSTRUCTIONS:
- Make sure to include this specific date ({formatted_date}) in the title
- Format the title as '# Title Here' with a single # symbol at the beginning
- Use proper markdown heading levels: # for title, ## for main sections, ### for subsections
- Do NOT use bold (**text**) for section headings, use proper heading levels instead
- Ensure consistent spacing between sections (one blank line before each heading)
- ALWAYS include proper citations for each paper in the spotlight section
- Make sure each citation includes authors, year, title, and URL in markdown format
- Format citations as: "**Citation:** Author1, Author2, et al. (2025). [Paper Title](paper URL)."
"""
        
        summary = summarize_with_gemini(paper_data, custom_prompt=custom_prompt)
        
        # Extract title from the summary (find the first line that starts with #)
        title_line = ""
        for line in summary.strip().split('\n'):
            if line.strip().startswith('#'):
                title_line = line.strip('#').strip()
                break
                
        # If no title found, check the first few lines
        if not title_line:
            first_lines = summary.strip().split('\n')[:5]
            for line in first_lines:
                if len(line.strip()) > 10 and not line.startswith('*') and not line.startswith('-'):
                    title_line = line.strip()
                    break
        
        # Check if the title already contains a date
        if "2025-04-26" in title_line:
            # Replace the incorrect date with the correct one
            title_line = title_line.replace("2025-04-26", formatted_date)
        
        if not title_line or len(title_line) < 10:  # Fallback if no clear title
            title = f"AI Breakthroughs This Week - {formatted_date}"
        else:
            title = title_line
            
        # Ensure the title doesn't have markdown formatting in the database
        title = title.replace('#', '').replace('*', '').strip()
        
        # Generate a catchy description based on the content
        try:
            # Extract the first paragraph after the title (usually the introduction)
            paragraphs = [p.strip() for p in summary.split('\n\n') if p.strip()]
            intro_paragraph = ""
            for p in paragraphs[1:3]:  # Look at the first few paragraphs after the title
                if len(p) > 100 and not p.startswith('#') and not p.startswith('*'):
                    intro_paragraph = p
                    break
            
            if intro_paragraph:
                # Extract a catchy sentence from the intro
                sentences = intro_paragraph.split('. ')
                catchy_sentence = next((s for s in sentences if len(s) > 50 and len(s) < 150), sentences[0])
                
                # Create a catchy description
                description = f"{catchy_sentence}. Explore this and more in our AI digest for {formatted_date}."
            else:
                # Fallback to a more generic but date-specific description
                description = f"Cutting-edge AI research from {formatted_date}: breakthroughs in machine learning, computer vision, and natural language processing that are shaping our future."
        except Exception as e:
            logger.warning(f"Error generating catchy description: {str(e)}")
            # Fallback description
            description = f"Discover the latest AI innovations and breakthroughs in this week's digest, published on {formatted_date}."
        
        # Print the newsletter with engaging formatting
        print("\n")
        print("="*100)
        print(title.center(100))
        print("="*100)
        print("\n")
        print(summary)
        print("\n")
        print("="*100)
        print("© AI Insights Weekly".center(100))
        print("="*100)
        
        # Save to database with the specific date
        summary_id = save_to_database(title, summary, description, date)
        
        logger.info(f"Newsletter generation for {formatted_date} completed successfully with ID: {summary_id}")
        print(f"\nNewsletter for {formatted_date} saved to database with ID: {summary_id}")
        print(f"View at: http://localhost:8000/content?summary_id={summary_id}")
        
    except Exception as e:
        logger.error(f"Error generating newsletter for date {date.strftime('%Y-%m-%d')}: {str(e)}")
        print(f"Error generating newsletter for date {date.strftime('%Y-%m-%d')}: {str(e)}")

def main():
    """Main function to run the script."""
    try:
        # Generate newsletters for April 20-26, 2025
        dates = [
            datetime.datetime(2025, 4, 20),
            datetime.datetime(2025, 4, 21),
            datetime.datetime(2025, 4, 22),
            datetime.datetime(2025, 4, 23),
            datetime.datetime(2025, 4, 24),
            datetime.datetime(2025, 4, 25),
            datetime.datetime(2025, 4, 26)
        ]
        
        for date in dates:
            logger.info(f"Generating newsletter for {date.strftime('%Y-%m-%d')}")
            
            # Generate newsletter for this date
            generate_newsletter_for_date(date)
            
            # Add a delay between API calls to avoid rate limiting
            if date != dates[-1]:  # Don't sleep after the last one
                logger.info("Sleeping for 5 seconds to avoid API rate limiting...")
                time.sleep(5)
        
        logger.info("Newsletter generation completed successfully")
        print("\nNewsletters for April 20-26, 2025 have been generated and saved to the database")
        
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
