from database import SessionLocal
from models import Newsletter
import datetime

def update_newsletter_dates():
    # Create a database session
    db = SessionLocal()
    
    try:
        # Get newsletters with IDs 6 and 7
        newsletters = db.query(Newsletter).filter(Newsletter.summary_id.in_([6, 7])).all()
        
        # Update the dates to 2025
        for newsletter in newsletters:
            # Extract the month and day from the current date
            current_date = newsletter.date
            month = current_date.month
            day = current_date.day
            
            # Create a new date in 2025 with the same month and day
            new_date = datetime.datetime(2025, month, day)
            
            # Update the newsletter date
            newsletter.date = new_date
            
            print(f"Updated newsletter {newsletter.summary_id} date from {current_date} to {new_date}")
        
        # Commit the changes
        db.commit()
        print("Changes committed to database")
        
    except Exception as e:
        print(f"Error updating dates: {str(e)}")
        db.rollback()
    finally:
        # Close the database session
        db.close()

if __name__ == "__main__":
    update_newsletter_dates()
