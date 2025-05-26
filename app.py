import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
import os

# Database functions
def init_db():
    conn = sqlite3.connect('detailing.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_plate TEXT NOT NULL,
            detail_type TEXT NOT NULL,
            advisor TEXT NOT NULL,
            location TEXT NOT NULL,
            hours REAL NOT NULL,
            entry_date DATE NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

def add_entry(conn, license_plate, detail_type, advisor, location, hours, entry_date, notes=""):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO entries (license_plate, detail_type, advisor, location, hours, entry_date, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (license_plate.upper().strip(), detail_type, advisor.strip(), location, hours, entry_date, notes.strip()))
    conn.commit()
    return True

def get_entries(conn, limit=50):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM entries 
        ORDER BY entry_date DESC, created_at DESC 
        LIMIT ?
    ''', (limit,))
    return cursor.fetchall()

def get_stats(conn):
    cursor = conn.cursor()
    
    # Total entries
    cursor.execute("SELECT COUNT(*) FROM entries")
    total = cursor.fetchone()[0]
    
    # Total hours
    cursor.execute("SELECT COALESCE(SUM(hours), 0) FROM entries")
    total_hours = cursor.fetchone()[0]
    
    # Today's entries
    today = date.today().strftime('%Y-%m-%d')
    cursor.execute("SELECT COUNT(*) FROM entries WHERE entry_date = ?", (today,))
    today_count = cursor.fetchone()[0]
    
    # Today's hours
    cursor.execute("SELECT COALESCE(SUM(hours), 0) FROM entries WHERE entry_date = ?", (today,))
    today_hours = cursor.fetchone()[0]
    
    return {
        'total': total,
        'total_hours': round(total_hours, 1),
        'today': today_count,
        'today_hours': round(today_hours, 1)
    }

# Main app
def main():
    st.set_page_config(
        page_title="Auto Detailing Tracker",
        page_icon="🚗",
        layout="wide"
    )
    
    # Header
    st.markdown("""
    <div style="background: linear-gradient(90deg, #2563eb 0%, #3b82f6 100%); padding: 1rem; border-radius: 0.5rem; margin-bottom: 2rem; color: white; text-align: center;">
        <h1>🚗 Auto Detailing Time Tracker</h1>
        <p>Professional detailing workflow management for dealerships</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize database
    if 'db_conn' not in st.session_state:
        st.session_state.db_conn = init_db()
    
    conn = st.session_state.db_conn
    
    # Navigation tabs
    tab1, tab2, tab3 = st.tabs(["🏠 Dashboard", "📝 New Entry", "📋 View Log"])
    
    with tab1:
        show_dashboard(conn)
    
    with tab2:
        show_new_entry(conn)
    
    with tab3:
        show_log(conn)

def show_dashboard(conn):
    stats = get_stats(conn)
    
    # Today's progress
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #2563eb; margin-bottom: 1rem;">
        <h3 style="margin: 0 0 1rem 0; color: #374151;">Today's Progress</h3>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; text-align: center;">
            <div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #2563eb;">{stats['today']}</div>
                <div style="font-size: 0.875rem; color: #6b7280;">Cars</div>
            </div>
            <div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #059669;">{stats['today_hours']}</div>
                <div style="font-size: 0.875rem; color: #6b7280;">Hours</div>
            </div>
            <div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #dc2626;">{stats['total']}</div>
                <div style="font-size: 0.875rem; color: #6b7280;">Total</div>
            </div>
            <div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #7c3aed;">{stats['total_hours']}</div>
                <div style="font-size: 0.875rem; color: #6b7280;">All Hours</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚗 Quick New Entry", use_container_width=True, type="primary"):
            st.switch_page("📝 New Entry")
    
    with col2:
        if st.button("📋 View Full Log", use_container_width=True):
            st.switch_page("📋 View Log")
    
    with col3:
        entries = get_entries(conn, 1000)
        if entries and st.button("📊 Export Data", use_container_width=True):
            df = pd.DataFrame(entries, columns=['ID', 'License Plate', 'Type', 'Advisor', 'Location', 'Hours', 'Date', 'Notes', 'Created'])
            csv = df.to_csv(index=False)
            st.download_button(
                "📁 Download CSV",
                csv,
                f"detailing_entries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv",
                use_container_width=True
            )
    
    # Recent entries
    st.subheader("Recent Entries")
    entries = get_entries(conn, 5)
    
    if entries:
        for entry in entries:
            hours_color = "#dc2626" if entry[5] > 3 else "#374151"
            st.markdown(f"""
            <div style="background: #f8fafc; padding: 1rem; border-radius: 0.5rem; border: 1px solid #e2e8f0; margin-bottom: 0.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <div style="font-weight: 600; font-size: 1rem;">{entry[1]}</div>
                        <div style="color: #6b7280; font-size: 0.875rem;">{entry[2]} • {entry[3]}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-weight: bold; color: {hours_color};">{entry[5]}h</div>
                        <div style="color: #6b7280; font-size: 0.75rem;">{entry[4]}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No entries yet. Add your first entry to get started!")

def show_new_entry(conn):
    st.header("Add New Entry")
    
    st.info("💡 Common notes: Pet hair removal, Extra polish needed, Heavy cleaning required, Minor touch-up, Leather conditioning, Paint correction")
    
    with st.form("new_entry"):
        license_plate = st.text_input("License Plate *", placeholder="ABC-123")
        
        detail_type = st.selectbox("Detail Type *", [
            "New Vehicle Delivery",
            "CPO/Used Vehicle", 
            "Customer Car",
            "Showroom Detail",
            "Demo Vehicle",
            "Full Detail",
            "Interior Detail",
            "Exterior Detail",
            "Polish & Wax",
            "Basic Wash",
            "Engine Bay",
            "Other"
        ])
        
        advisor = st.text_input("Advisor/Detailer Name *", placeholder="Enter name")
        
        location = st.selectbox("Location *", [
            "Bay 1", "Bay 2", "Bay 3", "Bay 4",
            "Outside", "Service Lane", "Wash Bay", "Detail Shop"
        ])
        
        hours = st.number_input("Hours *", min_value=0.1, max_value=24.0, step=0.1, value=1.0)
        
        entry_date = st.date_input("Date *", value=date.today())
        
        notes = st.text_area("Notes (Optional)", placeholder="Additional details, issues, or special instructions...")
        
        submitted = st.form_submit_button("➕ Add Entry", type="primary", use_container_width=True)
    
    if submitted:
        if not license_plate or not license_plate.strip():
            st.error("❌ License plate is required")
        elif not advisor or not advisor.strip():
            st.error("❌ Advisor name is required")
        elif hours <= 0:
            st.error("❌ Hours must be greater than 0")
        else:
            try:
                success = add_entry(conn, license_plate, detail_type, advisor, location, hours, str(entry_date), notes)
                if success:
                    st.success(f"✅ Entry added successfully for {license_plate.upper()}")
                    st.balloons()
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")

def show_log(conn):
    st.header("Entry Log")
    
    entries = get_entries(conn, 100)
    
    if entries:
        stats = get_stats(conn)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Entries", stats['total'])
        with col2:
            st.metric("Total Hours", f"{stats['total_hours']}h")
        with col3:
            avg_hours = stats['total_hours'] / max(stats['total'], 1)
            st.metric("Average Hours", f"{avg_hours:.1f}h")
        
        st.divider()
        
        for entry in entries:
            hours_color = "#dc2626" if entry[5] > 3 else "#374151"
            notes_text = f'<div style="color: #4b5563; font-size: 0.75rem; margin-top: 0.25rem; font-style: italic;">{entry[7][:100]}{"..." if len(entry[7] or "") > 100 else ""}</div>' if entry[7] else ''
            
            st.markdown(f"""
            <div style="background: #f8fafc; padding: 1rem; border-radius: 0.5rem; border: 1px solid #e2e8f0; margin-bottom: 0.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <div style="font-weight: 600; font-size: 1rem; margin-bottom: 0.25rem;">{entry[1]}</div>
                        <div style="color: #6b7280; font-size: 0.875rem; margin-bottom: 0.25rem;">{entry[2]} • {entry[3]}</div>
                        <div style="color: #9ca3af; font-size: 0.75rem;">{entry[6]} • {entry[4]}</div>
                        {notes_text}
                    </div>
                    <div style="text-align: right; margin-left: 1rem;">
                        <div style="font-weight: bold; color: {hours_color}; font-size: 1.25rem;">{entry[5]}h</div>
                        <div style="color: #6b7280; font-size: 0.75rem;">ID: {entry[0]}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        if st.button("📥 Export All Entries", use_container_width=True):
            df = pd.DataFrame(entries, columns=['ID', 'License Plate', 'Type', 'Advisor', 'Location', 'Hours', 'Date', 'Notes', 'Created'])
            csv = df.to_csv(index=False)
            st.download_button(
                "📁 Download CSV File",
                csv,
                f"detailing_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv",
                use_container_width=True
            )
    else:
        st.info("No entries found. Add your first entry to get started!")

if __name__ == "__main__":
    main()