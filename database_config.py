"""
Database configuration for Vehicle Hour Tracker
Supports both SQLite (local) and Supabase PostgreSQL (cloud)
"""

import os
import sqlite3
import tempfile
import json
from datetime import datetime
import streamlit as st

# Try to import requests and postgrest - gracefully handle if not available
try:
    import requests
    from postgrest import APIClient
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

def get_database_config():
    """Get database configuration from environment or Streamlit secrets"""
    config = {
        'use_supabase': False,
        'supabase_url': None,
        'supabase_key': None
    }
    
    # Check environment variables first
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    # Check Streamlit secrets if env vars not found
    if not supabase_url or not supabase_key:
        try:
            if hasattr(st, 'secrets') and 'supabase' in st.secrets:
                supabase_url = st.secrets.supabase.get('url')
                supabase_key = st.secrets.supabase.get('anon_key')
        except Exception:
            pass
    
    # Enable Supabase if credentials are available
    if SUPABASE_AVAILABLE and supabase_url and supabase_key:
        config.update({
            'use_supabase': True,
            'supabase_url': supabase_url,
            'supabase_key': supabase_key
        })
    
    return config

def get_supabase_client():
    """Create and return simple Supabase REST client"""
    config = get_database_config()
    if not config['use_supabase']:
        return None
    
    try:
        # Create simple REST client
        client = {
            'url': config['supabase_url'],
            'key': config['supabase_key'],
            'headers': {
                'apikey': config['supabase_key'],
                'Authorization': f"Bearer {config['supabase_key']}",
                'Content-Type': 'application/json'
            }
        }
        return client
    except Exception as e:
        st.error(f"Failed to create Supabase client: {e}")
        return None

def init_supabase_schema(client):
    """Check if Supabase database schema exists"""
    try:
        # Simple test query to check if table exists
        url = f"{client['url']}/rest/v1/entries?select=id&limit=1"
        response = requests.get(url, headers=client['headers'])
        return response.status_code == 200
    except Exception as e:
        st.error(f"Supabase schema check failed: {e}")
        st.info("Please create the 'entries' table in your Supabase dashboard with the following SQL:")
        st.code("""
CREATE TABLE entries (
    id BIGSERIAL PRIMARY KEY,
    license_plate TEXT NOT NULL,
    detail_type TEXT NOT NULL,
    advisor TEXT NOT NULL,
    hours REAL NOT NULL,
    entry_date DATE NOT NULL,
    notes TEXT,
    photos TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add indexes for better performance
CREATE INDEX idx_entries_entry_date ON entries(entry_date DESC);
CREATE INDEX idx_entries_created_at ON entries(created_at DESC);
CREATE INDEX idx_entries_license_plate ON entries(license_plate);
        """)
        return False

def get_database_connection():
    """Get database connection - Supabase if available, otherwise SQLite"""
    config = get_database_config()
    
    if config['use_supabase']:
        supabase = get_supabase_client()
        if supabase and init_supabase_schema(supabase):
            return supabase, 'supabase'
    
    # Fallback to SQLite
    return init_sqlite_db(), 'sqlite'

def init_sqlite_db():
    """Initialize SQLite database (fallback)"""
    db_path = 'detail_log.db'
    
    try:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.execute('PRAGMA journal_mode=DELETE')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                license_plate TEXT NOT NULL,
                detail_type TEXT NOT NULL,
                advisor TEXT NOT NULL,
                hours REAL NOT NULL,
                entry_date DATE NOT NULL,
                notes TEXT,
                photos TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Auto-cleanup entries older than 60 days for SQLite
        cursor.execute('''
            DELETE FROM entries 
            WHERE created_at < datetime('now', '-60 days')
        ''')
        
        conn.commit()
        return conn
    except Exception as e:
        st.error(f"SQLite initialization failed: {e}")
        # Return in-memory database as last resort
        conn = sqlite3.connect(':memory:', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                license_plate TEXT NOT NULL,
                detail_type TEXT NOT NULL,
                advisor TEXT NOT NULL,
                hours REAL NOT NULL,
                entry_date DATE NOT NULL,
                notes TEXT,
                photos TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        return conn