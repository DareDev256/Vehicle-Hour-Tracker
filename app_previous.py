import streamlit as st
import pandas as pd
from datetime import datetime, date
from database import DetailingDatabase

# Initialize database
@st.cache_resource
def init_database():
    try:
        return DetailingDatabase()
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

def main():
    st.set_page_config(
        page_title="Auto Detailing Time Tracker",
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
    
    db = init_database()
    if not db:
        st.stop()
    
    # Navigation
    tab1, tab2, tab3 = st.tabs(["🏠 Dashboard", "📝 New Entry", "📋 View Log"])
    
    with tab1:
        show_dashboard(db)
    with tab2:
        show_new_entry(db)
    with tab3:
        show_log(db)

def show_dashboard(db):
    try:
        stats = db.get_summary_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Today's Entries", stats['today_entries'])
        with col2:
            st.metric("Today's Hours", f"{stats['today_hours']:.1f}h")
        with col3:
            st.metric("Total Entries", stats['total_entries'])
        with col4:
            st.metric("Total Hours", f"{stats['total_hours']:.1f}h")
        
        st.subheader("Recent Entries")
        entries = db.get_recent_entries(5)
        
        if entries:
            for entry in entries:
                st.write(f"**{entry['license_plate']}** - {entry['detail_type']} - {entry['advisor']} - {entry['hours']}h")
        else:
            st.info("No entries yet. Add your first entry!")
            
    except Exception as e:
        st.error(f"Dashboard error: {e}")

def show_new_entry(db):
    st.header("Add New Entry")
    
    # Simple form without st.form to avoid button conflicts
    license_plate = st.text_input("License Plate", placeholder="ABC-123")
    
    detail_type = st.selectbox("Detail Type", [
        "Full Detail", "Interior Detail", "Exterior Detail", 
        "Polish & Wax", "Basic Wash", "Engine Bay"
    ])
    
    advisor = st.text_input("Advisor/Detailer Name", placeholder="Enter name")
    
    location = st.selectbox("Location", [
        "Bay 1", "Bay 2", "Bay 3", "Outside", "Detail Shop"
    ])
    
    hours = st.number_input("Hours", min_value=0.1, max_value=24.0, step=0.1, value=1.0)
    
    entry_date = st.date_input("Date", value=date.today())
    
    notes = st.text_area("Notes (Optional)", placeholder="Additional details...")
    
    if st.button("Add Entry", type="primary", use_container_width=True):
        if not license_plate:
            st.error("License plate is required")
        elif not advisor:
            st.error("Advisor name is required")
        else:
            try:
                success = db.add_entry(
                    license_plate=license_plate.strip(),
                    detail_type=detail_type,
                    advisor=advisor.strip(),
                    location=location,
                    hours=hours,
                    entry_date=str(entry_date),
                    notes=notes.strip()
                )
                
                if success:
                    st.success(f"Entry added for {license_plate.upper()}")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Failed to add entry")
            except Exception as e:
                st.error(f"Error: {e}")

def show_log(db):
    st.header("Entry Log")
    
    try:
        entries = db.get_recent_entries(50)
        
        if entries:
            # Convert to DataFrame for display
            data = []
            for entry in entries:
                data.append({
                    'License Plate': entry['license_plate'],
                    'Type': entry['detail_type'],
                    'Advisor': entry['advisor'],
                    'Location': entry['location'],
                    'Hours': entry['hours'],
                    'Date': entry['entry_date'],
                    'Notes': entry['notes'] or ''
                })
            
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Export
            if st.button("Export to CSV"):
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    f"detailing_log_{datetime.now().strftime('%Y%m%d')}.csv",
                    "text/csv"
                )
        else:
            st.info("No entries found")
            
    except Exception as e:
        st.error(f"Log error: {e}")

if __name__ == "__main__":
    main()