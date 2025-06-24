"""
Simple Supabase integration for Vehicle Hour Tracker
Uses basic REST calls instead of complex SDK
"""

import os
import json
from datetime import datetime
import streamlit as st

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None

class SimpleSupabase:
    def __init__(self):
        self.url = None
        self.key = None
        self.headers = None
        self.enabled = False
        self._init_connection()
    
    def _init_connection(self):
        """Initialize Supabase connection if credentials available"""
        if not REQUESTS_AVAILABLE:
            return
        
        # Try to get credentials from secrets or environment
        try:
            if hasattr(st, 'secrets') and 'supabase' in st.secrets:
                self.url = st.secrets.supabase.get('url')
                self.key = st.secrets.supabase.get('anon_key')
            else:
                self.url = os.getenv('SUPABASE_URL')
                self.key = os.getenv('SUPABASE_ANON_KEY')
            
            if self.url and self.key:
                self.headers = {
                    'apikey': self.key,
                    'Authorization': f'Bearer {self.key}',
                    'Content-Type': 'application/json'
                }
                self.enabled = True
        except Exception:
            pass
    
    def is_enabled(self):
        """Check if Supabase is properly configured"""
        return self.enabled and REQUESTS_AVAILABLE
    
    def test_connection(self):
        """Test if Supabase connection works"""
        if not self.is_enabled():
            return False
        
        try:
            url = f"{self.url}/rest/v1/entries?select=id&limit=1"
            response = requests.get(url, headers=self.headers, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def insert_entry(self, data):
        """Insert a new entry into Supabase"""
        if not self.is_enabled():
            return None
        
        try:
            url = f"{self.url}/rest/v1/entries"
            response = requests.post(url, headers=self.headers, json=data, timeout=10)
            if response.status_code == 201:
                return response.json()[0]['id']
            return None
        except Exception as e:
            st.error(f"Supabase insert failed: {e}")
            return None
    
    def get_entries(self, limit=1000):
        """Get all entries from Supabase"""
        if not self.is_enabled():
            return []
        
        try:
            url = f"{self.url}/rest/v1/entries?order=entry_date.desc,created_at.desc&limit={limit}"
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            st.error(f"Supabase fetch failed: {e}")
            return []
    
    def update_entry(self, entry_id, data):
        """Update an entry in Supabase"""
        if not self.is_enabled():
            return False
        
        try:
            url = f"{self.url}/rest/v1/entries?id=eq.{entry_id}"
            response = requests.patch(url, headers=self.headers, json=data, timeout=10)
            return response.status_code == 204
        except Exception as e:
            st.error(f"Supabase update failed: {e}")
            return False
    
    def delete_entry(self, entry_id):
        """Delete an entry from Supabase"""
        if not self.is_enabled():
            return False
        
        try:
            url = f"{self.url}/rest/v1/entries?id=eq.{entry_id}"
            response = requests.delete(url, headers=self.headers, timeout=10)
            return response.status_code == 204
        except Exception as e:
            st.error(f"Supabase delete failed: {e}")
            return False

# Global instance
supabase = SimpleSupabase()