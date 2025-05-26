import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date

def init_db():
    """Initialize SQLite database"""
    conn = sqlite3.connect('detailing.db', check_same_thread=False)
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
    conn.commit()
    return conn

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
    
    # Navigation
    tab1, tab2, tab3 = st.tabs(["🏠 Dashboard", "📝 New Entry", "📋 View Log"])
    
    with tab1:
        show_dashboard(conn)
    
    with tab2:
        show_new_entry(conn)
    
    with tab3:
        show_log(conn)

def show_dashboard(conn):
    """Show dashboard with stats and recent entries"""
    cursor = conn.cursor()
    
    # Get stats
    cursor.execute("SELECT COUNT(*) FROM entries")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COALESCE(SUM(hours), 0) FROM entries")
    total_hours = cursor.fetchone()[0]
    
    today = date.today().strftime('%Y-%m-%d')
    cursor.execute("SELECT COUNT(*) FROM entries WHERE entry_date = ?", (today,))
    today_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COALESCE(SUM(hours), 0) FROM entries WHERE entry_date = ?", (today,))
    today_hours = cursor.fetchone()[0]
    
    # Display stats
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #2563eb; margin-bottom: 1rem;">
        <h3 style="margin: 0 0 1rem 0; color: #374151;">Today's Progress</h3>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; text-align: center;">
            <div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #2563eb;">{today_count}</div>
                <div style="font-size: 0.875rem; color: #6b7280;">Cars Today</div>
            </div>
            <div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #059669;">{today_hours:.1f}</div>
                <div style="font-size: 0.875rem; color: #6b7280;">Hours Today</div>
            </div>
            <div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #dc2626;">{total}</div>
                <div style="font-size: 0.875rem; color: #6b7280;">Total Entries</div>
            </div>
            <div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #7c3aed;">{total_hours:.1f}</div>
                <div style="font-size: 0.875rem; color: #6b7280;">Total Hours</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick actions
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🚗 Quick New Entry**")
        st.write("Click the New Entry tab to add a detailing record")
    
    with col2:
        st.markdown("**📋 View Full Log**")
        st.write("Click the View Log tab to see all entries")
    
    with col3:
        st.markdown("**📊 Export Data**")
        cursor.execute("SELECT * FROM entries ORDER BY entry_date DESC")
        entries = cursor.fetchall()
        if entries:
            # Create DataFrame without specifying columns to avoid mismatch
            df = pd.DataFrame(entries)
            # Set proper column names based on actual data
            df.columns = ['ID', 'License Plate', 'Type', 'Advisor', 'Hours', 'Date', 'Notes', 'Created'] if len(df.columns) == 8 else ['ID', 'License Plate', 'Type', 'Advisor', 'Location', 'Hours', 'Date', 'Notes', 'Created']
            # Remove location column if it exists
            if 'Location' in df.columns:
                df = df.drop('Location', axis=1)
            csv = df.to_csv(index=False)
            st.download_button(
                "📁 Download CSV",
                csv,
                f"detailing_entries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv",
                use_container_width=True
            )
        else:
            st.write("No data to export yet")
    
    # Recent entries
    st.subheader("Recent Entries")
    cursor.execute("SELECT * FROM entries ORDER BY entry_date DESC, created_at DESC LIMIT 5")
    entries = cursor.fetchall()
    
    if entries:
        for entry in entries:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                
                with col1:
                    st.write(f"**{entry[1]}**")  # License Plate
                    st.caption(f"{entry[2]}")  # Detail Type
                
                with col2:
                    st.write(f"{entry[3]}")  # Advisor Name
                
                with col3:
                    st.write(f"{entry[5]}")  # Date
                
                with col4:
                    hours_color = "🔴" if float(entry[4]) > 3 else "⏱️"  # Hours
                    st.write(f"{hours_color} {entry[4]}h")
                
                st.divider()
    else:
        st.info("No entries yet. Add your first entry to get started!")

def show_new_entry(conn):
    """Show new entry form"""
    st.header("Add New Entry")
    
    st.info("💡 Common notes: Pet hair removal, Extra polish needed, Heavy cleaning required, Minor touch-up, Leather conditioning, Paint correction")
    
    with st.form("new_entry_form"):
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
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO entries (license_plate, detail_type, advisor, hours, entry_date, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (license_plate.upper().strip(), detail_type, advisor.strip(), hours, str(entry_date), notes.strip()))
                conn.commit()
                
                # Show success message with entry details
                st.success(f"✅ Entry added successfully!")
                st.info(f"**{license_plate.upper()}** • {detail_type} • {advisor} • {hours}h • {entry_date}")
                st.balloons()
                
                # Wait a moment for user to see the feedback, then refresh
                import time
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error adding entry: {e}")

def show_log(conn):
    """Show all entries log"""
    st.header("Entry Log")
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM entries ORDER BY entry_date DESC, created_at DESC")
    entries = cursor.fetchall()
    
    if entries:
        # Stats
        total_hours = sum(float(entry[4]) for entry in entries)  # Hours are at index 4
        avg_hours = total_hours / len(entries) if entries else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Entries", len(entries))
        with col2:
            st.metric("Total Hours", f"{total_hours:.1f}h")
        with col3:
            st.metric("Average Hours", f"{avg_hours:.1f}h")
        
        st.divider()
        
        # Display entries in clean format
        st.subheader("Entry Log (Newest First)")
        
        # Header row
        col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 1.5, 1, 1])
        with col1:
            st.write("**License Plate**")
        with col2:
            st.write("**Detail Type**")
        with col3:
            st.write("**Detailer**")
        with col4:
            st.write("**Date**")
        with col5:
            st.write("**Hours**")
        with col6:
            st.write("**ID**")
        
        st.divider()
        
        for entry in entries:
            col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 1.5, 1, 1])
            
            with col1:
                st.write(f"**{entry[1]}**")  # License Plate
            
            with col2:
                st.write(f"{entry[2]}")  # Detail Type
            
            with col3:
                st.write(f"{entry[3]}")  # Advisor/Detailer Name
            
            with col4:
                st.write(f"{entry[5]}")  # Date
            
            with col5:
                hours_indicator = "🔴" if float(entry[4]) > 3 else "⏱️"  # Hours
                st.write(f"{hours_indicator} {entry[4]}h")
            
            with col6:
                st.write(f"#{entry[0]}")  # Entry ID
            
            # Show notes if they exist
            if entry[6]:  # Notes (adjusted index)
                st.caption(f"📝 {entry[6][:100]}{'...' if len(entry[6]) > 100 else ''}")
            
            st.divider()
        
        # Export option
        st.divider()
        # Create DataFrame without specifying columns to avoid mismatch
        df = pd.DataFrame(entries)
        # Set proper column names based on actual data
        df.columns = ['ID', 'License Plate', 'Type', 'Advisor', 'Hours', 'Date', 'Notes', 'Created'] if len(df.columns) == 8 else ['ID', 'License Plate', 'Type', 'Advisor', 'Location', 'Hours', 'Date', 'Notes', 'Created']
        # Remove location column if it exists
        if 'Location' in df.columns:
            df = df.drop('Location', axis=1)
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Export All Entries to CSV",
            csv,
            f"detailing_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "text/csv",
            use_container_width=True
        )
    else:
        st.info("No entries found. Add your first entry to get started!")

if __name__ == "__main__":
    main()