"""
Database Cleanup Script

This script clears all data from the database tables without dropping the tables themselves.
It preserves the database structure while removing all records.

Usage:
    python clear_database.py
"""

import os
import sys
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our database configuration
from database import engine, Base, SessionLocal
from models import User, Newsletter, Research, Paper, UserUpload, Chat, NewsletterPodcast, CustomPaperPodcast

def clear_all_tables():
    """Clear all data from all tables in the database."""
    session = SessionLocal()
    
    try:
        # Define the order of tables to clear (respecting foreign key constraints)
        tables_to_clear = [
            Chat,                # Has foreign keys to multiple tables
            UserUpload,          # Has foreign keys to User and Paper
            NewsletterPodcast,   # Has foreign key to Newsletter
            CustomPaperPodcast,  # Has foreign key to Paper
            Paper,               # Referenced by other tables
            Newsletter,          # Referenced by other tables
            Research,            # Independent table
            # User                 # Referenced by other tables
        ]
        
        # Clear each table
        for table in tables_to_clear:
            print(f"Clearing table: {table.__tablename__}")
            session.query(table).delete()
        
        # Commit the changes
        session.commit()
        print("All tables have been cleared successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"Error clearing tables: {str(e)}")
    finally:
        session.close()

def clear_specific_table(table_name):
    """Clear data from a specific table."""
    session = SessionLocal()
    
    # Map table names to model classes
    table_map = {
        # 'users': User,
        'newsletter': Newsletter,
        'research': Research,
        'papers': Paper,
        'user_uploads': UserUpload,
        'chats': Chat,
        'newsletter_podcasts': NewsletterPodcast,
        'custom_paper_podcasts': CustomPaperPodcast
    }
    
    if table_name not in table_map:
        print(f"Error: Table '{table_name}' not found. Available tables: {', '.join(table_map.keys())}")
        return
    
    try:
        model = table_map[table_name]
        print(f"Clearing table: {model.__tablename__}")
        session.query(model).delete()
        session.commit()
        print(f"Table '{table_name}' has been cleared successfully!")
    except Exception as e:
        session.rollback()
        print(f"Error clearing table '{table_name}': {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Clear data from database tables.')
    parser.add_argument('--table', type=str, help='Specific table to clear (omit to clear all tables)')
    
    args = parser.parse_args()
    
    if args.table:
        clear_specific_table(args.table)
    else:
        # Confirm before clearing all tables
        confirm = input("This will clear ALL DATA from ALL TABLES. Are you sure? (y/n): ")
        if confirm.lower() == 'y':
            clear_all_tables()
        else:
            print("Operation cancelled.")
