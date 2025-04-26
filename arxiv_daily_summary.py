#!/usr/bin/env python3
"""
ArXiv Daily Summary Generator

This script fetches the latest AI research papers from arXiv,
summarizes them using Google's Gemini API, highlights the most important ones,
and saves the result to the newsletter database.
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyAsH6fY-voLT1WP4PgZL0b2nA3gZqoz6WQ"
genai.configure(api_key=GEMINI_API_KEY)

def fetch_arxiv_papers(max_results: int = 200) -> List[arxiv.Result]:
    """
    Fetch the latest AI-related papers from arXiv.

    Args:
        max_results: Maximum number of papers to fetch

    Returns:
        List of arXiv Result objects
    """
    logger.info(f"Fetching up to {max_results} papers from arXiv...")

    # Create a search query for AI-related papers
    # Using categories: cs.AI (Artificial Intelligence), cs.LG (Machine Learning),
    # cs.CL (Computation and Language), cs.CV (Computer Vision)

    search = arxiv.Search(
        query="cat:cs.AI OR cat:cs.LG OR cat:cs.CL OR cat:cs.CV",
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )

    # Create a client with reasonable rate limits
    client = arxiv.Client(
        page_size=100,
        delay_seconds=3.0,
        num_retries=3
    )

    # Fetch the results
    results = list(client.results(search))
    logger.info(f"Successfully fetched {len(results)} papers from arXiv")

    return results

def prepare_paper_data(papers: List[arxiv.Result]) -> List[Dict[str, Any]]:
    """
    Extract relevant information from arXiv papers.

    Args:
        papers: List of arXiv Result objects

    Returns:
        List of dictionaries containing paper information
    """
    paper_data = []

    for paper in papers:
        # Extract paper information
        data = {
            "title": paper.title,
            "authors": [author.name for author in paper.authors],
            "summary": paper.summary,
            "published": paper.published.strftime("%Y-%m-%d"),
            "url": paper.entry_id,
            "pdf_url": paper.pdf_url,
            "categories": paper.categories
        }
        paper_data.append(data)

    return paper_data

def summarize_with_gemini(papers: List[Dict[str, Any]], custom_prompt: str = None) -> str:
    """
    Use Gemini API to summarize the papers and highlight important ones.

    Args:
        papers: List of dictionaries containing paper information
        custom_prompt: Optional custom prompt to use for summarization

    Returns:
        A string containing the summarized content
    """
    logger.info("Summarizing papers with Gemini API...")

    # Create a prompt for Gemini
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    # Prepare paper information for the prompt
    papers_text = ""
    for i, paper in enumerate(papers, 1):
        papers_text += f"Paper {i}:\n"
        papers_text += f"Title: {paper['title']}\n"
        papers_text += f"Authors: {', '.join(paper['authors'])}\n"
        papers_text += f"Published: {paper['published']}\n"
        papers_text += f"Categories: {', '.join(paper['categories'])}\n"
        papers_text += f"Summary: {paper['summary']}\n"
        papers_text += f"URL: {paper['url']}\n\n"

    # Prepare the prompt
    if custom_prompt:
        prompt_prefix = custom_prompt
    else:
        prompt_prefix = f"""
        You are a professional science communicator specializing in making artificial intelligence research accessible to a general audience.

        Today is {today}, and I'll provide you with the latest research papers from arXiv in AI, ML, Computer Vision, and NLP.

        Your task is to create an engaging, thoughtful newsletter for a general audience interested in AI developments.
        """

    prompt = f"""{prompt_prefix}

    The newsletter should:
    1. Start with a main title using a single # symbol (e.g., "# Main Title Here")
    2. Include an introduction that explains the significance of these papers
    3. Have a section titled "## Major Trends" (using ## for heading level 2) that identifies 2-3 major trends across the papers
    4. Have a section titled "## Spotlight on Five Interesting Papers" (using ## for heading level 2) that highlights 5 particularly interesting papers with:
       - A level 3 heading (###) for each paper title
       - A brief explanation of what the paper is about in simple terms
       - Why it matters to the average person
       - An analogy to help understand the concept
    5. End with a section titled "## Conclusion" (using ## for heading level 2) with a forward-looking conclusion

    IMPORTANT FORMATTING INSTRUCTIONS:
    - Use proper markdown heading levels: # for title, ## for main sections, ### for subsections
    - Do NOT use bold (**text**) for section headings, use proper heading levels instead
    - Ensure consistent spacing between sections (one blank line before each heading)
    - Make sure the title is properly formatted as "# Title Here" with the # symbol
    - Use proper markdown for emphasis: **bold** for important terms and *italic* for emphasis
    - Format the newsletter with clear hierarchical structure using proper heading levels

    Format the newsletter to be engaging and accessible to a general audience while maintaining scientific accuracy.

    Here are today's papers:

    {papers_text}
    """

    try:
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-2.0-flash')

        # Generate response
        response = model.generate_content(prompt)

        return response.text
    except Exception as e:
        logger.error(f"Error generating summary with Gemini: {str(e)}")
        return f"Error generating summary: {str(e)}"



def save_to_database(title: str, content: str, description: str) -> int:
    """
    Save the generated content to the newsletter database.

    Args:
        title: The title of the newsletter
        content: The content of the newsletter
        description: A brief description of the newsletter

    Returns:
        The ID of the newly created newsletter entry
    """
    logger.info("Saving content to database...")

    try:
        # Create a database session
        db = SessionLocal()

        # Generate a unique filename for the image
        image_filename = f"{hashlib.md5(title.encode()).hexdigest()}.jpg"
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
                    logger.info("Successfully downloaded themed image")
                else:
                    logger.error(f"Failed to download themed image: HTTP {response.status_code}")
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
            date=datetime.datetime.now()
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

def main():
    """Main function to run the script."""
    try:
        # Fetch papers from arXiv (try to get up to 200 papers)
        try:
            papers = fetch_arxiv_papers(max_results=200)
        except Exception as e:
            logger.warning(f"Error fetching all papers: {str(e)}. Trying with fewer papers.")
            # Try with fewer papers
            papers = fetch_arxiv_papers(max_results=100)

        # Prepare paper data
        paper_data = prepare_paper_data(papers)

        # Ensure we have at least some papers
        if not paper_data:
            raise ValueError("No papers were fetched from arXiv")

        logger.info(f"Processing {len(paper_data)} papers for today's digest")

        # Summarize papers with Gemini
        summary = summarize_with_gemini(paper_data)

        # Get today's date for the header
        today = datetime.datetime.now().strftime("%Y-%m-%d")

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
            title_line = title_line.replace("2025-04-26", today)

        if not title_line or len(title_line) < 10:  # Fallback if no clear title
            title = f"AI Breakthroughs This Week - {today}"
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
                description = f"{catchy_sentence}. Explore this and more in our AI digest for {today}."
            else:
                # Fallback to a more generic but date-specific description
                description = f"Cutting-edge AI research from {today}: breakthroughs in machine learning, computer vision, and natural language processing that are shaping our future."
        except Exception as e:
            logger.warning(f"Error generating catchy description: {str(e)}")
            # Fallback description
            description = f"Discover the latest AI innovations and breakthroughs in this week's digest, published on {today}."

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

        # Save to database
        summary_id = save_to_database(title, summary, description)

        logger.info(f"Newsletter generation completed successfully with ID: {summary_id}")
        print(f"\nNewsletter saved to database with ID: {summary_id}")
        print(f"View at: http://localhost:8000/content?summary_id={summary_id}")

    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
