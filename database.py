import psycopg2
import psycopg2.extras
import os
from datetime import datetime
from typing import List, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DetailingDatabase:
    def __init__(self, db_url: str = None):
        """Initialize the database connection and create tables if they don't exist."""
        self.db_url = db_url or os.getenv('DATABASE_URL')
        self.init_database()
    
    def get_connection(self):
        """Get a database connection with proper settings."""
        conn = psycopg2.connect(self.db_url)
        return conn
    
    def init_database(self):
        """Create the database tables if they don't exist."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create detailing entries table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS detailing_entries (
                        id SERIAL PRIMARY KEY,
                        license_plate VARCHAR(20) NOT NULL,
                        detail_type VARCHAR(100) NOT NULL,
                        advisor VARCHAR(100) NOT NULL,
                        location VARCHAR(100) NOT NULL,
                        hours DECIMAL(5,2) NOT NULL,
                        entry_date DATE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        notes TEXT
                    )
                """)
                
                # Create index for faster queries
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_entry_date 
                    ON detailing_entries(entry_date DESC)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_license_plate 
                    ON detailing_entries(license_plate)
                """)
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except psycopg2.Error as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def add_entry(self, license_plate: str, detail_type: str, advisor: str, 
                  location: str, hours: float, entry_date: str, notes: str = "") -> bool:
        """Add a new detailing entry to the database."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO detailing_entries 
                    (license_plate, detail_type, advisor, location, hours, entry_date, notes)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (license_plate.upper().strip(), detail_type, advisor.strip(), 
                      location, hours, entry_date, notes.strip()))
                
                conn.commit()
                logger.info(f"Added entry for license plate: {license_plate}")
                return True
                
        except psycopg2.Error as e:
            logger.error(f"Error adding entry: {e}")
            return False
    
    def get_recent_entries(self, limit: int = 50) -> List[dict]:
        """Get recent detailing entries, ordered by date (most recent first)."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                
                cursor.execute("""
                    SELECT id, license_plate, detail_type, advisor, location, 
                           hours, entry_date, created_at, notes
                    FROM detailing_entries 
                    ORDER BY entry_date DESC, created_at DESC
                    LIMIT %s
                """, (limit,))
                
                return cursor.fetchall()
                
        except psycopg2.Error as e:
            logger.error(f"Error fetching recent entries: {e}")
            return []
    
    def get_entries_by_date_range(self, start_date: str, end_date: str) -> List[sqlite3.Row]:
        """Get entries within a specific date range."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, license_plate, detail_type, advisor, location, 
                           hours, entry_date, created_at, notes
                    FROM detailing_entries 
                    WHERE entry_date BETWEEN ? AND ?
                    ORDER BY entry_date DESC, created_at DESC
                """, (start_date, end_date))
                
                return cursor.fetchall()
                
        except sqlite3.Error as e:
            logger.error(f"Error fetching entries by date range: {e}")
            return []
    
    def get_entries_by_license_plate(self, license_plate: str) -> List[sqlite3.Row]:
        """Get all entries for a specific license plate."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, license_plate, detail_type, advisor, location, 
                           hours, entry_date, created_at, notes
                    FROM detailing_entries 
                    WHERE license_plate = ?
                    ORDER BY entry_date DESC, created_at DESC
                """, (license_plate.upper().strip(),))
                
                return cursor.fetchall()
                
        except sqlite3.Error as e:
            logger.error(f"Error fetching entries by license plate: {e}")
            return []
    
    def get_summary_stats(self) -> dict:
        """Get summary statistics for the dashboard."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Total entries
                cursor.execute("SELECT COUNT(*) FROM detailing_entries")
                total_entries = cursor.fetchone()[0]
                
                # Total hours
                cursor.execute("SELECT SUM(hours) FROM detailing_entries")
                total_hours = cursor.fetchone()[0] or 0
                
                # Today's entries
                today = datetime.now().strftime('%Y-%m-%d')
                cursor.execute("SELECT COUNT(*) FROM detailing_entries WHERE entry_date = ?", (today,))
                today_entries = cursor.fetchone()[0]
                
                # Today's hours
                cursor.execute("SELECT SUM(hours) FROM detailing_entries WHERE entry_date = ?", (today,))
                today_hours = cursor.fetchone()[0] or 0
                
                # Most common detail type
                cursor.execute("""
                    SELECT detail_type, COUNT(*) as count 
                    FROM detailing_entries 
                    GROUP BY detail_type 
                    ORDER BY count DESC 
                    LIMIT 1
                """)
                result = cursor.fetchone()
                most_common_type = result[0] if result else "N/A"
                
                return {
                    'total_entries': total_entries,
                    'total_hours': round(total_hours, 2),
                    'today_entries': today_entries,
                    'today_hours': round(today_hours, 2),
                    'most_common_type': most_common_type
                }
                
        except sqlite3.Error as e:
            logger.error(f"Error fetching summary stats: {e}")
            return {
                'total_entries': 0,
                'total_hours': 0,
                'today_entries': 0,
                'today_hours': 0,
                'most_common_type': 'N/A'
            }
    
    def update_entry(self, entry_id: int, license_plate: str, detail_type: str, 
                     advisor: str, location: str, hours: float, entry_date: str, 
                     notes: str = "") -> bool:
        """Update an existing detailing entry."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE detailing_entries 
                    SET license_plate = ?, detail_type = ?, advisor = ?, 
                        location = ?, hours = ?, entry_date = ?, notes = ?
                    WHERE id = ?
                """, (license_plate.upper().strip(), detail_type, advisor.strip(), 
                      location, hours, entry_date, notes.strip(), entry_id))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Updated entry ID: {entry_id}")
                    return True
                else:
                    logger.warning(f"No entry found with ID: {entry_id}")
                    return False
                
        except sqlite3.Error as e:
            logger.error(f"Error updating entry: {e}")
            return False
    
    def delete_entry(self, entry_id: int) -> bool:
        """Delete a detailing entry."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM detailing_entries WHERE id = ?", (entry_id,))
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"Deleted entry ID: {entry_id}")
                    return True
                else:
                    logger.warning(f"No entry found with ID: {entry_id}")
                    return False
                
        except sqlite3.Error as e:
            logger.error(f"Error deleting entry: {e}")
            return False
