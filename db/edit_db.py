import sqlite3
import datetime
import os

def get_utc_now():
    """Helper function to get the current UTC datetime."""
    return datetime.datetime.utcnow()

def main():
    """Main function to connect to the database, insert data, and verify."""

    # --- 1. Construct the Absolute Database Path ---
    # Get the directory of the current script
    script_dir = os.path.dirname(__file__)
    # Construct the full path to the database file
    db_path = os.path.join(script_dir, "", "research.db")

    # --- 2. Check if the Database File Exists ---
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return  # Exit if the database file doesn't exist

    # --- 3. Connect to the Database (with Error Handling) ---
    conn = None  # Initialize conn to None for the finally block
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # --- 4. (Optional) List Tables for Verification ---
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables in database:", tables)

        # --- 5. Print Original Data (Optional) ---
        cursor.execute("SELECT * FROM newsletter;")
        print("Original Data:", cursor.fetchall())  # Print existing data

        # --- 6. Insert Dummy Data into Newsletter Table ---

        # Prepare a list of tuples, each representing a new newsletter entry
        new_newsletters = [
            (
                "AI in Healthcare: Breakthroughs of 2024",
                get_utc_now(),
                "https://example.com/images/paper1.jpg",
                "This newsletter covers the latest advancements in AI applications within healthcare, including diagnostics, treatment planning, and patient care.",
                "AI advancements in diagnostics and treatment.",
            ),
            (
                "The Future of Quantum Computing",
                get_utc_now(),
                "https://example.com/images/paper2.jpg",
                "Explore the cutting-edge developments in quantum computing, discussing recent breakthroughs, potential applications, and challenges.",
                "Quantum computing breakthroughs and applications.",
            ),
            (
                "Climate Change Research: A Comprehensive Overview",
                get_utc_now(),
                "https://example.com/images/paper3.jpg",
                "This newsletter provides a summary of the most impactful research papers on climate change published recently, covering impacts, mitigation, and adaptation strategies.",
                "Summary of recent climate change research.",
            ),
            (
                "Neuroscience Advances: Understanding the Brain",
                get_utc_now(),
                "https://example.com/images/paper1.jpg",
                "Dive into the latest findings in neuroscience, exploring new understandings of brain function, neurological disorders, and potential therapies.",
                "Latest findings in neuroscience and brain function.",
            ),
            (
                "Sustainable Energy Technologies: Innovations and Challenges",
                get_utc_now(),
                "https://example.com/images/paper2.jpg",
                "This newsletter focuses on innovations in sustainable energy technologies, including solar, wind, and energy storage, discussing both progress and obstacles.",
                "Innovations in solar, wind, and energy storage.",
            ),
            (
                "Space Exploration Update: Missions and Discoveries",
                get_utc_now(),
                "https://example.com/images/paper3.jpg",
                "Get updated on the latest space exploration missions, discoveries, and future plans from various space agencies around the globe.",
                "Latest missions, and future plans in space"
            ),
             (
                "Biotechnology Breakthrough: Gene Editing and Beyond",
                get_utc_now(),
                "https://example.com/images/paper1.jpg",
                "This issue covers new developments in gene editing and related biotechnologies, focusing on their potential applications, as well as potential issues.",
                "New developments in gene editing"
            )
        ]

        # Insert the new data
        cursor.executemany(
            "INSERT INTO newsletter (title, date, picture, content, description) VALUES (?, ?, ?, ?, ?)",
            new_newsletters,
        )
        conn.commit()  # Commit the changes

        # --- 7. Verification: Print the Updated Table ---
        cursor.execute("SELECT * FROM newsletter;")
        print("\nNew Data:", cursor.fetchall())  # Print the updated table

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")

    finally:
        # --- 8. Close the Connection (Always!) ---
        if conn:  # Check if conn was successfully created
            conn.close()
            print("Connection closed.")

if __name__ == "__main__":
    main()