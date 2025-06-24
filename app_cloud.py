import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
import os
from PIL import Image
import tempfile
from io import BytesIO

# Configure Streamlit page - MUST be first Streamlit command
st.set_page_config(
    page_title="Vehicle Hour Tracker",
    page_icon="🚗",
    layout="wide"
)

@st.cache_resource
def init_database():
    """Initialize SQLite database with error handling"""
    try:
        # Use in-memory database for Streamlit Cloud reliability
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add sample data for demo
        cursor.execute('''
            INSERT OR IGNORE INTO entries (license_plate, detail_type, advisor, hours, entry_date, notes)
            VALUES ('ABC123', 'Full Detail', 'John Doe', 3.5, '2024-06-23', 'Sample entry for demo')
        ''')
        
        conn.commit()
        return conn
    except Exception as e:
        st.error(f"Database initialization failed: {e}")
        return None

def add_entry(conn, license_plate, detail_type, advisor, hours, entry_date, notes):
    """Add new entry to database"""
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO entries (license_plate, detail_type, advisor, hours, entry_date, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (license_plate.upper().strip(), detail_type, advisor.strip(), hours, str(entry_date), notes.strip()))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error adding entry: {e}")
        return False

def get_all_entries(conn):
    """Get all entries from database"""
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM entries ORDER BY entry_date DESC, created_at DESC")
        return cursor.fetchall()
    except Exception as e:
        st.error(f"Error fetching entries: {e}")
        return []

def delete_entry(conn, entry_id):
    """Delete entry from database"""
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        st.error(f"Error deleting entry: {e}")
        return False

def show_entry_form(conn):
    """Show the entry form"""
    st.subheader("➕ Add New Entry")
    
    with st.form("entry_form"):
        # Input fields
        license_plate = st.text_input("🚗 License Plate", placeholder="ABC123")
        
        detail_type = st.selectbox("🧽 Detail Type", 
                                 ["Quick Wash", "Standard Detail", "Full Detail", "Premium Detail"])
        
        advisor = st.text_input("👤 Detailer/Advisor", placeholder="Enter name")
        
        hours = st.number_input("⏰ Hours Worked", min_value=0.1, max_value=24.0, value=1.0, step=0.5)
        
        entry_date = st.date_input("📅 Service Date", value=date.today())
        
        notes = st.text_area("📝 Notes & Comments", 
                           placeholder="Customer requests, damage notes, special instructions...",
                           height=100)
        
        # Submit button
        submitted = st.form_submit_button("✅ Add Entry", type="primary", use_container_width=True)
    
    if submitted:
        if not license_plate or not license_plate.strip():
            st.error("❌ License plate is required")
        elif not advisor or not advisor.strip():
            st.error("❌ Detailer name is required")
        elif hours <= 0:
            st.error("❌ Hours must be greater than 0")
        else:
            if add_entry(conn, license_plate, detail_type, advisor, hours, entry_date, notes):
                st.success("✅ Entry added successfully!")
                st.rerun()

def show_log(conn):
    """Show all entries"""
    st.subheader("📋 View All Entries")
    
    entries = get_all_entries(conn)
    
    if entries:
        # Stats
        total_entries = len(entries)
        total_hours = sum(entry[4] for entry in entries)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Entries", total_entries)
        with col2:
            st.metric("Total Hours", f"{total_hours:.1f}h")
        with col3:
            st.metric("Average Hours", f"{total_hours/total_entries:.1f}h")
        
        st.divider()
        
        # Display entries
        for entry in entries:
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"### {entry[1]}")
                    st.markdown(f"**{entry[2]}** • {entry[3]}")
                    st.caption(f"📅 {entry[5]}")
                    if entry[6]:
                        st.markdown(f"*{entry[6][:100]}{'...' if len(entry[6] or '') > 100 else ''}*")
                
                with col2:
                    hours_color = "🟢" if float(entry[4]) <= 1 else "🟡" if float(entry[4]) <= 3 else "🟠" if float(entry[4]) <= 6 else "🔴"
                    st.markdown(f"**{hours_color} {entry[4]}h**")
                    st.caption(f"ID: #{entry[0]}")
                    
                    if st.button("🗑️", key=f"delete_{entry[0]}", help="Delete entry"):
                        if delete_entry(conn, entry[0]):
                            st.success("✅ Entry deleted!")
                            st.rerun()
                
                st.divider()
    else:
        st.info("🎯 No entries found. Add your first detailing entry to get started!")

def show_export(conn):
    """Show export options"""
    st.subheader("📥 Export Data")
    
    entries = get_all_entries(conn)
    
    if entries:
        # Prepare data for export
        data = []
        for entry in entries:
            data.append({
                'ID': entry[0],
                'License Plate': entry[1],
                'Detail Type': entry[2],
                'Advisor': entry[3],
                'Hours': entry[4],
                'Service Date': entry[5],
                'Notes': entry[6] or '',
                'Created At': entry[7] if len(entry) > 7 else ''
            })
        
        df = pd.DataFrame(data)
        
        # CSV Export
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Download CSV",
            csv,
            f"detailing_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv",
            use_container_width=True
        )
        
        # Data preview
        st.subheader("📊 Data Preview")
        st.dataframe(df, use_container_width=True)
        
    else:
        st.info("🎯 No entries found. Add your first detailing entry to get started!")

def main():
    """Main application"""
    # App title
    st.title("🚗 Vehicle Hour Tracker")
    st.markdown("Track detailing hours and manage service records")
    
    # Initialize database
    conn = init_database()
    
    if not conn:
        st.error("❌ Failed to initialize database. Please refresh the page.")
        st.stop()
    
    # Navigation
    nav_selection = st.sidebar.selectbox(
        "📍 Navigation",
        ["New Entry", "View Log", "Export Data"]
    )
    
    # Route to appropriate function
    if nav_selection == "New Entry":
        show_entry_form(conn)
    elif nav_selection == "View Log":
        show_log(conn)
    elif nav_selection == "Export Data":
        show_export(conn)

# Run the app
if __name__ == "__main__":
    main()
else:
    # This ensures the app runs when imported by Streamlit Cloud
    main()