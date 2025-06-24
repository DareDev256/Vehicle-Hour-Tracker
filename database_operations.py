"""
Database operations that work with both SQLite and Supabase
"""

import os
import tempfile
import json
from datetime import datetime
import streamlit as st
from database_config import get_database_connection

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

class DatabaseOperations:
    def __init__(self):
        self.conn, self.db_type = get_database_connection()
        
    def insert_entry(self, license_plate, detail_type, advisor, hours, entry_date, notes='', photos=''):
        """Insert a new entry"""
        try:
            if self.db_type == 'supabase':
                result = self.conn.table('entries').insert({
                    'license_plate': license_plate.upper().strip(),
                    'detail_type': detail_type,
                    'advisor': advisor.strip(),
                    'hours': hours,
                    'entry_date': str(entry_date),
                    'notes': notes.strip(),
                    'photos': photos
                }).execute()
                return result.data[0]['id'] if result.data else None
            else:
                # SQLite
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO entries (license_plate, detail_type, advisor, hours, entry_date, notes, photos)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (license_plate.upper().strip(), detail_type, advisor.strip(), hours, str(entry_date), notes.strip(), photos))
                self.conn.commit()
                return cursor.lastrowid
        except Exception as e:
            st.error(f"Error inserting entry: {e}")
            return None
    
    def get_all_entries(self):
        """Get all entries"""
        try:
            if self.db_type == 'supabase':
                result = self.conn.table('entries').select('*').order('entry_date', desc=True).order('created_at', desc=True).execute()
                return result.data if result.data else []
            else:
                # SQLite
                cursor = self.conn.cursor()
                cursor.execute("SELECT * FROM entries ORDER BY entry_date DESC, created_at DESC")
                return cursor.fetchall()
        except Exception as e:
            st.error(f"Error fetching entries: {e}")
            return []
    
    def get_entries_by_date_filter(self, filter_option):
        """Get entries based on date filter"""
        try:
            if self.db_type == 'supabase':
                # Supabase queries
                if filter_option == "Today":
                    result = self.conn.table('entries').select('*').gte('entry_date', 'now()').order('entry_date', desc=True).execute()
                elif filter_option == "Last 7 Days":
                    result = self.conn.table('entries').select('*').gte('entry_date', 'now() - interval \'7 days\'').order('entry_date', desc=True).execute()
                elif filter_option == "Last 30 Days":
                    result = self.conn.table('entries').select('*').gte('entry_date', 'now() - interval \'30 days\'').order('entry_date', desc=True).execute()
                elif filter_option == "Last 60 Days":
                    result = self.conn.table('entries').select('*').gte('entry_date', 'now() - interval \'60 days\'').order('entry_date', desc=True).execute()
                else:  # All
                    result = self.conn.table('entries').select('*').order('entry_date', desc=True).execute()
                return result.data if result.data else []
            else:
                # SQLite
                cursor = self.conn.cursor()
                if filter_option == "Today":
                    query = "SELECT * FROM entries WHERE DATE(entry_date) = DATE('now') ORDER BY entry_date DESC, created_at DESC"
                elif filter_option == "Last 7 Days":
                    query = "SELECT * FROM entries WHERE entry_date >= DATE('now', '-7 days') ORDER BY entry_date DESC, created_at DESC"
                elif filter_option == "Last 30 Days":
                    query = "SELECT * FROM entries WHERE entry_date >= DATE('now', '-30 days') ORDER BY entry_date DESC, created_at DESC"
                elif filter_option == "Last 60 Days":
                    query = "SELECT * FROM entries WHERE entry_date >= DATE('now', '-60 days') ORDER BY entry_date DESC, created_at DESC"
                else:  # All
                    query = "SELECT * FROM entries ORDER BY entry_date DESC, created_at DESC"
                
                cursor.execute(query)
                return cursor.fetchall()
        except Exception as e:
            st.error(f"Error fetching filtered entries: {e}")
            return []
    
    def get_entry_by_id(self, entry_id):
        """Get a single entry by ID"""
        try:
            if self.db_type == 'supabase':
                result = self.conn.table('entries').select('*').eq('id', entry_id).execute()
                return result.data[0] if result.data else None
            else:
                # SQLite
                cursor = self.conn.cursor()
                cursor.execute("SELECT * FROM entries WHERE id = ?", (entry_id,))
                return cursor.fetchone()
        except Exception as e:
            st.error(f"Error fetching entry: {e}")
            return None
    
    def update_entry(self, entry_id, license_plate, detail_type, advisor, hours, entry_date, notes):
        """Update an existing entry"""
        try:
            if self.db_type == 'supabase':
                result = self.conn.table('entries').update({
                    'license_plate': license_plate.upper().strip(),
                    'detail_type': detail_type,
                    'advisor': advisor.strip(),
                    'hours': hours,
                    'entry_date': str(entry_date),
                    'notes': notes.strip()
                }).eq('id', entry_id).execute()
                return len(result.data) > 0
            else:
                # SQLite
                cursor = self.conn.cursor()
                cursor.execute('''
                    UPDATE entries 
                    SET license_plate = ?, detail_type = ?, advisor = ?, hours = ?, 
                        entry_date = ?, notes = ?
                    WHERE id = ?
                ''', (license_plate.upper().strip(), detail_type, advisor.strip(), hours, str(entry_date), notes.strip(), entry_id))
                self.conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            st.error(f"Error updating entry: {e}")
            return False
    
    def delete_entry(self, entry_id):
        """Delete an entry and its associated photos"""
        try:
            # Get photos before deleting
            entry = self.get_entry_by_id(entry_id)
            if entry:
                # Handle photos deletion (for SQLite, we have photos stored locally)
                if self.db_type == 'sqlite' and len(entry) > 7 and entry[7]:
                    photos_dir = self.get_photos_dir()
                    photo_files = entry[7].split(',')
                    for photo_file in photo_files:
                        if photo_file.strip():
                            photo_path = os.path.join(photos_dir, photo_file.strip())
                            try:
                                if os.path.exists(photo_path):
                                    os.remove(photo_path)
                            except Exception as e:
                                st.warning(f"Failed to delete photo {photo_file}: {e}")
            
            # Delete the entry
            if self.db_type == 'supabase':
                result = self.conn.table('entries').delete().eq('id', entry_id).execute()
                return len(result.data) > 0
            else:
                # SQLite
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
                self.conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            st.error(f"Error deleting entry: {e}")
            return False
    
    def update_photos(self, entry_id, photos):
        """Update photos for an entry"""
        try:
            if self.db_type == 'supabase':
                result = self.conn.table('entries').update({'photos': photos}).eq('id', entry_id).execute()
                return len(result.data) > 0
            else:
                # SQLite
                cursor = self.conn.cursor()
                cursor.execute('UPDATE entries SET photos = ? WHERE id = ?', (photos, entry_id))
                self.conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            st.error(f"Error updating photos: {e}")
            return False
    
    def clear_all_entries(self):
        """Clear all entries"""
        try:
            if self.db_type == 'supabase':
                result = self.conn.table('entries').delete().neq('id', 0).execute()  # Delete all
                return True
            else:
                # SQLite
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM entries")
                self.conn.commit()
                return True
        except Exception as e:
            st.error(f"Error clearing entries: {e}")
            return False
    
    def get_stats(self):
        """Get basic statistics"""
        try:
            if self.db_type == 'supabase':
                # Get counts and sums
                result = self.conn.table('entries').select('id, hours, photos').execute()
                if result.data:
                    total_entries = len(result.data)
                    total_hours = sum(float(entry.get('hours', 0)) for entry in result.data)
                    avg_hours = total_hours / total_entries if total_entries > 0 else 0
                    with_photos = sum(1 for entry in result.data if entry.get('photos'))
                    return total_entries, total_hours, avg_hours, with_photos
                return 0, 0, 0, 0
            else:
                # SQLite
                cursor = self.conn.cursor()
                cursor.execute("SELECT COUNT(*), COALESCE(SUM(hours), 0), COALESCE(AVG(hours), 0) FROM entries")
                total_entries, total_hours, avg_hours = cursor.fetchone()
                
                cursor.execute("SELECT COUNT(*) FROM entries WHERE photos IS NOT NULL AND photos != ''")
                with_photos = cursor.fetchone()[0]
                
                return total_entries, total_hours, avg_hours, with_photos
        except Exception as e:
            st.error(f"Error getting stats: {e}")
            return 0, 0, 0, 0
    
    def get_photos_dir(self):
        """Get the photos directory path, cloud-compatible"""
        photos_dir = 'photos'
        try:
            if not os.path.exists(photos_dir):
                os.makedirs(photos_dir, exist_ok=True)
            return photos_dir
        except (OSError, PermissionError):
            # Fallback to temp directory for cloud deployment
            fallback_dir = os.path.join(tempfile.gettempdir(), 'streamlit_photos')
            os.makedirs(fallback_dir, exist_ok=True)
            return fallback_dir