#!/usr/bin/env python3
"""
Safe startup version of app.py with comprehensive error handling
This version will help debug Streamlit Cloud deployment issues
"""

import sys
import traceback
from datetime import datetime

def log_startup_error(error_msg, exception=None):
    """Log startup errors for debugging"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] STARTUP ERROR: {error_msg}")
    if exception:
        print(f"Exception details: {str(exception)}")
        traceback.print_exc()

def safe_import():
    """Safely import all required modules"""
    try:
        import streamlit as st
        import sqlite3
        import pandas as pd
        from datetime import datetime, date
        import os
        from PIL import Image
        import json
        import tempfile
        return True, (st, sqlite3, pd, datetime, date, os, Image, json, tempfile)
    except ImportError as e:
        log_startup_error(f"Import failed: {e}", e)
        return False, None
    except Exception as e:
        log_startup_error(f"Unexpected import error: {e}", e)
        return False, None

def safe_init_db(sqlite3, os, tempfile, st):
    """Initialize database with comprehensive error handling"""
    try:
        # Try multiple database path strategies
        db_paths = []
        
        # Strategy 1: Home directory
        try:
            home = os.path.expanduser('~')
            if home != '~' and os.access(home, os.W_OK):
                db_paths.append(os.path.join(home, 'detail_log.db'))
        except:
            pass
        
        # Strategy 2: Current directory
        try:
            if os.access('.', os.W_OK):
                db_paths.append('./detail_log.db')
        except:
            pass
        
        # Strategy 3: Temp directory
        try:
            temp_dir = tempfile.gettempdir()
            db_paths.append(os.path.join(temp_dir, 'detail_log.db'))
        except:
            pass
        
        # Strategy 4: In-memory (fallback)
        db_paths.append(':memory:')
        
        conn = None
        for db_path in db_paths:
            try:
                print(f"Trying database path: {db_path}")
                conn = sqlite3.connect(db_path, check_same_thread=False)
                
                # Test the connection
                cursor = conn.cursor()
                cursor.execute('SELECT 1')
                cursor.fetchone()
                
                # Set journal mode safely
                try:
                    conn.execute('PRAGMA journal_mode=DELETE')
                except:
                    print("Warning: Could not set journal mode")
                
                # Create table
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
                print(f"Database initialized successfully: {db_path}")
                break
                
            except Exception as e:
                if conn:
                    conn.close()
                print(f"Database path {db_path} failed: {e}")
                continue
        
        if not conn:
            raise Exception("All database initialization strategies failed")
        
        # Try to create photos directory
        try:
            photos_dirs = [
                os.path.join(os.path.expanduser('~'), 'photos'),
                './photos',
                os.path.join(tempfile.gettempdir(), 'streamlit_photos')
            ]
            
            for photos_dir in photos_dirs:
                try:
                    os.makedirs(photos_dir, exist_ok=True)
                    if os.access(photos_dir, os.W_OK):
                        print(f"Photos directory ready: {photos_dir}")
                        break
                except:
                    continue
        except Exception as e:
            print(f"Warning: Photos directory creation failed: {e}")
        
        return conn
        
    except Exception as e:
        log_startup_error(f"Database initialization failed: {e}", e)
        # Return in-memory database as absolute fallback
        try:
            return sqlite3.connect(':memory:', check_same_thread=False)
        except:
            return None

def create_minimal_app(st):
    """Create a minimal Streamlit app for testing"""
    st.set_page_config(
        page_title="Vehicle Hour Tracker - Debug Mode",
        page_icon="🔧",
        layout="wide"
    )
    
    st.title("🔧 Vehicle Hour Tracker - Debug Mode")
    st.success("✅ Streamlit is running successfully!")
    
    st.info("""
    **Debug Information:**
    - Streamlit server is responding
    - Basic imports are working
    - App initialization completed
    
    If you see this page, the deployment is working but there may be 
    issues with the full application features.
    """)
    
    # Show environment info
    import sys
    import os
    st.subheader("Environment Information")
    st.text(f"Python version: {sys.version}")
    st.text(f"Working directory: {os.getcwd()}")
    st.text(f"Home directory: {os.path.expanduser('~')}")
    
    # Test database
    st.subheader("Database Test")
    try:
        import sqlite3
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        cursor.execute('SELECT 1 as test')
        result = cursor.fetchone()
        conn.close()
        st.success("✅ SQLite database test passed")
    except Exception as e:
        st.error(f"❌ Database test failed: {e}")

def main():
    """Main function with comprehensive error handling"""
    try:
        print("Starting safe app initialization...")
        
        # Step 1: Import modules
        import_success, modules = safe_import()
        if not import_success:
            print("FATAL: Import failed, cannot start app")
            sys.exit(1)
        
        st, sqlite3, pd, datetime, date, os, Image, json, tempfile = modules
        print("✅ All modules imported successfully")
        
        # Step 2: Initialize database
        print("Initializing database...")
        conn = safe_init_db(sqlite3, os, tempfile, st)
        if not conn:
            print("WARNING: Database initialization failed, using minimal mode")
        else:
            print("✅ Database initialized successfully")
        
        # Step 3: Create Streamlit app
        print("Creating Streamlit app...")
        create_minimal_app(st)
        print("✅ Streamlit app created successfully")
        
    except Exception as e:
        log_startup_error(f"Fatal error in main(): {e}", e)
        
        # Try to show error in Streamlit if possible
        try:
            import streamlit as st
            st.error(f"Application failed to start: {e}")
            st.code(traceback.format_exc())
        except:
            print("Could not display error in Streamlit")
        
        sys.exit(1)

if __name__ == "__main__":
    main()