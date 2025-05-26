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
        st.error(f"Database initialization failed: {e}")
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
        
        # Today's progress card
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #2563eb; margin-bottom: 1rem;">
            <h3 style="margin: 0 0 1rem 0; color: #374151;">Today's Progress</h3>
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; text-align: center;">
                <div>
                    <div style="font-size: 1.5rem; font-weight: bold; color: #2563eb;">{stats['today_entries']}</div>
                    <div style="font-size: 0.875rem; color: #6b7280;">Cars</div>
                </div>
                <div>
                    <div style="font-size: 1.5rem; font-weight: bold; color: #059669;">{stats['today_hours']:.1f}</div>
                    <div style="font-size: 0.875rem; color: #6b7280;">Hours</div>
                </div>
                <div>
                    <div style="font-size: 1.5rem; font-weight: bold; color: #dc2626;">{stats['today_hours'] / max(stats['today_entries'], 1):.1f}</div>
                    <div style="font-size: 0.875rem; color: #6b7280;">Avg</div>
                </div>
                <div>
                    <div style="font-size: 1.5rem; font-weight: bold; color: #7c3aed;">$340</div>
                    <div style="font-size: 0.875rem; color: #6b7280;">Value</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick actions
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚗 Quick New Entry", use_container_width=True, type="primary"):
                st.session_state.switch_to_tab = "new_entry"
                st.rerun()
        
        with col2:
            if st.button("📋 View Full Log", use_container_width=True):
                st.session_state.switch_to_tab = "view_log"
                st.rerun()
        
        with col3:
            entries = db.get_recent_entries(1000)
            if entries and st.button("📊 Export Data", use_container_width=True):
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
                csv = df.to_csv(index=False)
                st.download_button(
                    "📁 Download CSV File",
                    csv,
                    f"detailing_entries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv",
                    use_container_width=True
                )
        
        # Recent entries
        st.subheader("Recent Entries")
        entries = db.get_recent_entries(5)
        
        if entries:
            for entry in entries:
                hours_color = "#dc2626" if entry['hours'] > 3 else "#374151"
                st.markdown(f"""
                <div style="background: #f8fafc; padding: 1rem; border-radius: 0.5rem; border: 1px solid #e2e8f0; margin-bottom: 0.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 1;">
                            <div style="font-weight: 600; font-size: 1rem;">{entry['license_plate']}</div>
                            <div style="color: #6b7280; font-size: 0.875rem;">{entry['detail_type']} • {entry['advisor']}</div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-weight: bold; color: {hours_color};">{entry['hours']}h</div>
                            <div style="color: #6b7280; font-size: 0.75rem;">{entry['location']}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No entries yet. Add your first entry to get started!")
            
    except Exception as e:
        st.error(f"Dashboard error: {e}")

def show_new_entry(db):
    st.header("Add New Entry")
    
    st.info("💡 Common notes: Pet hair removal, Extra polish needed, Heavy cleaning required, Minor touch-up, Leather conditioning, Paint correction")
    
    with st.form("entry_form", clear_on_submit=True):
        # Form fields
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
                success = db.add_entry(
                    license_plate=license_plate.strip(),
                    detail_type=detail_type,
                    advisor=advisor.strip(),
                    location=location,
                    hours=hours,
                    entry_date=str(entry_date),
                    notes=notes.strip() if notes else ""
                )
                
                if success:
                    st.success(f"✅ Entry added successfully for {license_plate.upper()}")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Failed to add entry. Please try again.")
            except Exception as e:
                st.error(f"❌ Error: {e}")

def show_log(db):
    st.header("Entry Log")
    
    try:
        entries = db.get_recent_entries(100)
        
        if entries:
            # Stats
            total_hours = sum(entry['hours'] for entry in entries)
            avg_hours = total_hours / len(entries) if entries else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Entries", len(entries))
            with col2:
                st.metric("Total Hours", f"{total_hours:.1f}h")
            with col3:
                st.metric("Average Hours", f"{avg_hours:.1f}h")
            
            st.divider()
            
            # Display entries
            for entry in entries:
                hours_color = "#dc2626" if entry['hours'] > 3 else "#374151"
                st.markdown(f"""
                <div style="background: #f8fafc; padding: 1rem; border-radius: 0.5rem; border: 1px solid #e2e8f0; margin-bottom: 0.5rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 1;">
                            <div style="font-weight: 600; font-size: 1rem; margin-bottom: 0.25rem;">{entry['license_plate']}</div>
                            <div style="color: #6b7280; font-size: 0.875rem; margin-bottom: 0.25rem;">{entry['detail_type']} • {entry['advisor']}</div>
                            <div style="color: #9ca3af; font-size: 0.75rem;">{entry['entry_date']} • {entry['location']}</div>
                            {f'<div style="color: #4b5563; font-size: 0.75rem; margin-top: 0.25rem; font-style: italic;">{entry["notes"][:100]}{"..." if len(entry["notes"] or "") > 100 else ""}</div>' if entry['notes'] else ''}
                        </div>
                        <div style="text-align: right; margin-left: 1rem;">
                            <div style="font-weight: bold; color: {hours_color}; font-size: 1.25rem;">{entry['hours']}h</div>
                            <div style="color: #6b7280; font-size: 0.75rem;">ID: {entry['id']}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Export
            st.divider()
            if st.button("📥 Export All Entries", use_container_width=True):
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
            
    except Exception as e:
        st.error(f"Log error: {e}")

if __name__ == "__main__":
    main()