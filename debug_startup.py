#!/usr/bin/env python3
"""
Debug script for Streamlit startup issues
This will help identify what's failing during app initialization
"""

import sys
import traceback
from datetime import datetime

def log_error(msg):
    """Log errors with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] ERROR: {msg}")

def test_imports():
    """Test all required imports"""
    print("=== Testing Imports ===")
    
    # Test core imports
    imports = [
        ('sqlite3', 'sqlite3'),
        ('pandas', 'pd'),
        ('datetime', 'datetime, date'),
        ('os', 'os'),
        ('json', 'json'),
        ('tempfile', 'tempfile')
    ]
    
    for module, alias in imports:
        try:
            exec(f"import {module}")
            print(f"✅ {module} - OK")
        except Exception as e:
            log_error(f"{module} import failed: {e}")
            return False
    
    # Test PIL
    try:
        from PIL import Image
        print("✅ PIL (Pillow) - OK")
    except Exception as e:
        log_error(f"PIL import failed: {e}")
        return False
    
    # Test Streamlit (critical)
    try:
        import streamlit as st
        print(f"✅ Streamlit {st.__version__} - OK")
    except Exception as e:
        log_error(f"Streamlit import failed: {e}")
        return False
    
    return True

def test_file_operations():
    """Test file system operations"""
    print("\n=== Testing File Operations ===")
    
    import os
    import tempfile
    
    # Test home directory access
    try:
        home = os.path.expanduser('~')
        if home != '~':
            print(f"✅ Home directory: {home}")
        else:
            print("⚠️ Home directory not accessible, using temp")
    except Exception as e:
        log_error(f"Home directory access failed: {e}")
    
    # Test temp directory
    try:
        temp_dir = tempfile.gettempdir()
        print(f"✅ Temp directory: {temp_dir}")
    except Exception as e:
        log_error(f"Temp directory access failed: {e}")
        return False
    
    # Test directory creation
    try:
        test_dir = os.path.join(temp_dir, 'streamlit_test')
        os.makedirs(test_dir, exist_ok=True)
        print(f"✅ Directory creation: {test_dir}")
        
        # Cleanup
        import shutil
        shutil.rmtree(test_dir)
    except Exception as e:
        log_error(f"Directory creation failed: {e}")
        return False
    
    return True

def test_database():
    """Test SQLite database operations"""
    print("\n=== Testing Database ===")
    
    try:
        import sqlite3
        import tempfile
        import os
        
        # Test in-memory database
        conn = sqlite3.connect(':memory:', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        conn.close()
        print("✅ In-memory SQLite - OK")
        
        # Test file database
        temp_dir = tempfile.gettempdir()
        db_path = os.path.join(temp_dir, 'test.db')
        
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.execute('PRAGMA journal_mode=DELETE')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        ''')
        conn.commit()
        conn.close()
        
        # Cleanup
        os.remove(db_path)
        print("✅ File SQLite - OK")
        
    except Exception as e:
        log_error(f"Database test failed: {e}")
        return False
    
    return True

def test_streamlit_config():
    """Test Streamlit configuration"""
    print("\n=== Testing Streamlit Config ===")
    
    try:
        import streamlit as st
        
        # This should not fail if Streamlit is properly installed
        st.set_page_config(
            page_title="Test",
            page_icon="🔧",
            layout="wide"
        )
        print("✅ Streamlit page config - OK")
        
    except Exception as e:
        log_error(f"Streamlit config failed: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🔧 Streamlit Startup Debug Tool")
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print("=" * 50)
    
    success = True
    
    success &= test_imports()
    success &= test_file_operations()
    success &= test_database()
    
    # Only test Streamlit config if imports worked
    if success:
        success &= test_streamlit_config()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed! App should start normally.")
    else:
        print("❌ Tests failed! Check errors above.")
    
    return success

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)