from database import SessionLocal
from models import Newsletter
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def delete_all_newsletters():
    """Delete all newsletters from the database."""
    logger.info("Deleting all newsletters from the database...")
    
    # Create a database session
    db = SessionLocal()
    
    try:
        # Count newsletters before deletion
        count_before = db.query(Newsletter).count()
        logger.info(f"Found {count_before} newsletters in the database")
        
        # Delete all newsletters
        db.query(Newsletter).delete()
        
        # Commit the changes
        db.commit()
        
        # Count newsletters after deletion
        count_after = db.query(Newsletter).count()
        logger.info(f"Successfully deleted all newsletters. {count_after} newsletters remaining.")
        
    except Exception as e:
        logger.error(f"Error deleting newsletters: {str(e)}")
        db.rollback()
    finally:
        # Close the database session
        db.close()

if __name__ == "__main__":
    delete_all_newsletters()
