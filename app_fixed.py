import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import DetailingDatabase
from utils import (
    validate_form_data, convert_entries_to_dataframe, format_hours,
    get_detail_types, get_locations, get_date_range_options,
    show_success_message, show_error_message, show_warning_message,
    export_to_csv, calculate_duration_stats, get_advisor_stats
)

# Initialize database
@st.cache_resource
def init_database():
    return DetailingDatabase()

def main():
    # Page configuration
    st.set_page_config(
        page_title="Auto Detailing Time Tracker",
        page_icon="🚗",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #2563eb 0%, #3b82f6 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .stat-card {
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2563eb;
        margin-bottom: 1rem;
    }
    .recent-entry {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e2e8f0;
        margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize database
    db = init_database()
    
    # Main header
    st.markdown("""
    <div class="main-header">
        <h1>🚗 Auto Detailing Time Tracker</h1>
        <p>Professional detailing workflow management for dealerships</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏠 Main Dashboard", "📝 New Entry", "📋 View Log", "🔍 Search", "📊 Reports"
    ])
    
    with tab1:
        show_main_dashboard_page(db)
    with tab2:
        show_new_entry_page(db)
    with tab3:
        show_view_entries_page(db)
    with tab4:
        show_search_filter_page(db)
    with tab5:
        show_reports_page(db)

def show_main_dashboard_page(db):
    """Main dashboard inspired by the wireframe design"""
    
    # Quick stats widget
    stats = db.get_summary_stats()
    
    st.markdown(f"""
    <div class="stat-card">
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
    
    # Quick actions section
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("🚗 Click 'New Entry' tab to add entries")
    
    with col2:
        st.info("📋 Click 'View Log' tab to see all entries")
    
    with col3:
        if st.button("📊 Export All Data", use_container_width=True):
            entries = db.get_recent_entries(limit=1000)
            if entries:
                df = convert_entries_to_dataframe(entries)
                csv_data = export_to_csv(df)
                st.download_button(
                    label="📁 Download CSV File",
                    data=csv_data,
                    file_name=f"detailing_entries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    
    # Recent entries section
    st.subheader("Recent Entries")
    recent_entries = db.get_recent_entries(limit=5)
    
    if recent_entries:
        for entry in recent_entries:
            hours_color = "#dc2626" if entry['hours'] > 3 else "#374151"
            st.markdown(f"""
            <div class="recent-entry">
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
        st.info("No entries found. Add your first detailing entry to get started!")

def show_new_entry_page(db):
    st.header("🚗 New Detail Entry")
    
    st.info("💡 Common notes: Pet hair removal, Extra polish needed, Heavy cleaning required, Minor touch-up, Leather conditioning, Paint correction")
    
    # Create form
    with st.form("new_entry_form", clear_on_submit=True):
        # Vehicle info section
        st.markdown("### Vehicle Information")
        col1, col2 = st.columns(2)
        
        with col1:
            license_plate = st.text_input(
                "License Plate *",
                placeholder="ABC-123",
                help="Enter the vehicle's license plate number"
            )
            
            stock_number = st.text_input(
                "Stock Number (Optional)",
                placeholder="Stock #",
                help="Internal stock number if available"
            )
        
        with col2:
            detail_type = st.selectbox(
                "Detail Type *",
                options=[
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
                    "Other"
                ],
                help="Select the type of detailing service"
            )
            
            advisor = st.text_input(
                "Detailer Name *",
                placeholder="Detailer name",
                help="Name of the person performing the detail work"
            )
        
        # Service details section  
        st.markdown("### Service Details")
        col3, col4 = st.columns(2)
        
        with col3:
            location = st.selectbox(
                "Location *",
                options=[
                    "Bay 1", "Bay 2", "Bay 3", "Bay 4",
                    "Outside", "Service Lane", "Wash Bay", "Detail Shop"
                ],
                help="Select where the detailing work will be performed"
            )
        
        with col4:
            hours = st.number_input(
                "Hours Listed *",
                min_value=0.0,
                max_value=24.0,
                step=0.1,
                value=0.0,
                help="Time spent on detailing (in hours)"
            )
        
        entry_date = st.date_input(
            "Service Date *",
            value=date.today(),
            help="Date when the detailing service was performed"
        )
        
        notes = st.text_area(
            "Additional Notes",
            placeholder="Additional details, issues, or special instructions...",
            help="Optional notes about the detailing service",
            height=100
        )
        
        # Form submit button
        submitted = st.form_submit_button("➕ Add Entry", use_container_width=True, type="primary")
        
        if submitted:
            # Validate form data
            if not license_plate or not license_plate.strip():
                show_error_message("License plate is required.")
            elif not advisor or not advisor.strip():
                show_error_message("Advisor name is required.")
            elif hours <= 0:
                show_error_message("Hours must be greater than 0.")
            else:
                try:
                    # Add entry to database
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
                        show_success_message(f"Entry added successfully for {license_plate.upper()}")
                        st.balloons()
                        st.rerun()
                    else:
                        show_error_message("Failed to add entry. Please check your database connection.")
                except Exception as e:
                    show_error_message(f"Database connection error: {str(e)}")
                    st.info("💡 Tip: Make sure your database is properly configured and accessible.")

def show_view_entries_page(db):
    st.header("📋 Complete Detail Log")
    
    # Get entries
    entries = db.get_recent_entries(limit=100)
    
    if entries:
        # Summary stats
        stats = calculate_duration_stats(entries)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div style="background: #dbeafe; padding: 1rem; border-radius: 0.5rem; text-align: center;">
                <div style="font-weight: bold; font-size: 1.5rem; color: #2563eb;">{len(entries)}</div>
                <div style="font-size: 0.75rem; color: #6b7280;">Total Entries</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background: #dcfce7; padding: 1rem; border-radius: 0.5rem; text-align: center;">
                <div style="font-weight: bold; font-size: 1.5rem; color: #059669;">{stats['total']:.1f}</div>
                <div style="font-size: 0.75rem; color: #6b7280;">Total Hours</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style="background: #fed7aa; padding: 1rem; border-radius: 0.5rem; text-align: center;">
                <div style="font-weight: bold; font-size: 1.5rem; color: #ea580c;">{stats['avg']:.1f}</div>
                <div style="font-size: 0.75rem; color: #6b7280;">Avg/Entry</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # Entry list
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
        
        # Export functionality
        st.divider()
        if st.button("📥 Download as CSV", use_container_width=True):
            df = convert_entries_to_dataframe(entries)
            csv_data = export_to_csv(df)
            st.download_button(
                label="📁 Download CSV File",
                data=csv_data,
                file_name=f"detailing_entries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    else:
        st.info("No entries found. Add your first detailing entry to get started!")

def show_search_filter_page(db):
    st.header("🔍 Search & Filter Entries")
    
    # Search by license plate
    search_plate = st.text_input("Search by License Plate:", placeholder="ABC-1234")
    
    if st.button("🔍 Search", use_container_width=True) and search_plate:
        entries = db.get_entries_by_license_plate(search_plate)
        
        if entries:
            st.success(f"Found {len(entries)} entries for {search_plate.upper()}")
            df = convert_entries_to_dataframe(entries)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.warning(f"No entries found for {search_plate.upper()}")

def show_reports_page(db):
    st.header("📊 Reports & Analytics")
    
    # Date range for reports
    col1, col2 = st.columns(2)
    
    with col1:
        report_start = st.date_input("Report Start Date:", value=date.today() - timedelta(days=30))
    
    with col2:
        report_end = st.date_input("Report End Date:", value=date.today())
    
    if st.button("📊 Generate Report", use_container_width=True):
        entries = db.get_entries_by_date_range(str(report_start), str(report_end))
        
        if entries:
            df = convert_entries_to_dataframe(entries)
            
            st.success(f"Report generated for {len(entries)} entries")
            
            # Summary statistics
            st.subheader("Summary Statistics")
            stats = calculate_duration_stats(entries)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Entries", len(entries))
            with col2:
                st.metric("Total Hours", f"{stats['total']:.1f}h")
            with col3:
                st.metric("Average Hours", f"{stats['avg']:.1f}h")
            with col4:
                st.metric("Max Hours", f"{stats['max']:.1f}h")
            
            # Display data
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.warning(f"No entries found from {report_start} to {report_end}")

if __name__ == "__main__":
    main()