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
    .quick-action-btn {
        background: #2563eb;
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 0.5rem;
        border: none;
        width: 100%;
        margin: 0.25rem 0;
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
    
    # Navigation tabs (horizontal instead of sidebar)
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
    
    # Quick stats widget (matching wireframe)
    stats = db.get_summary_stats()
    
    st.markdown("""
    <div class="stat-card">
        <h3 style="margin: 0 0 1rem 0; color: #374151;">Today's Progress</h3>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; text-align: center;">
            <div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #2563eb;">{}</div>
                <div style="font-size: 0.875rem; color: #6b7280;">Cars</div>
            </div>
            <div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #059669;">{:.1f}</div>
                <div style="font-size: 0.875rem; color: #6b7280;">Hours</div>
            </div>
            <div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #dc2626;">{:.1f}</div>
                <div style="font-size: 0.875rem; color: #6b7280;">Avg</div>
            </div>
            <div>
                <div style="font-size: 1.5rem; font-weight: bold; color: #7c3aed;">$340</div>
                <div style="font-size: 0.875rem; color: #6b7280;">Value</div>
            </div>
        </div>
    </div>
    """.format(
        stats['today_entries'], 
        stats['today_hours'],
        stats['today_hours'] / max(stats['today_entries'], 1)
    ), unsafe_allow_html=True)
    
    # Quick actions section
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚗 Quick New Entry", use_container_width=True, type="primary"):
            pass
    
    with col2:
        if st.button("📋 View Full Log", use_container_width=True):
            pass
    
    with col3:
        if st.button("📊 Export Data", use_container_width=True):
            pass
    
    # Recent entries section (matching wireframe style)
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
    
    # Quick notes section (outside form - matching wireframe)
    st.markdown("### Quick Notes")
    quick_notes = [
        "Pet hair removal", "Extra polish needed", "Heavy cleaning required",
        "Minor touch-up", "Leather conditioning", "Paint correction"
    ]
    
    # Initialize notes in session state if not exists
    if 'current_notes' not in st.session_state:
        st.session_state.current_notes = ""
    
    cols = st.columns(3)
    for i, note in enumerate(quick_notes):
        with cols[i % 3]:
            if st.button(f"+ {note}", key=f"note_{i}", use_container_width=True):
                if st.session_state.current_notes:
                    st.session_state.current_notes += f"{note}. "
                else:
                    st.session_state.current_notes = f"{note}. "
                st.rerun()
    
    # Create form with better styling
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
                placeholder="2.5",
                help="Time spent on detailing (in hours)"
            )
        
        entry_date = st.date_input(
            "Service Date *",
            value=date.today(),
            help="Date when the detailing service was performed"
        )
        
        notes = st.text_area(
            "Additional Notes",
            value=st.session_state.current_notes,
            placeholder="Additional details, issues, or special instructions...",
            help="Optional notes about the detailing service",
            height=100
        )
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            cancel = st.form_submit_button("Cancel", use_container_width=True)
        with col2:
            submitted = st.form_submit_button("➕ Add Entry", use_container_width=True, type="primary")
        
        if submitted:
            # Update session notes with form value
            st.session_state.current_notes = notes
            
            # Validate form data
            errors = validate_form_data(license_plate or "", detail_type, advisor or "", location, hours)
            
            if errors:
                for error in errors:
                    show_error_message(error)
            else:
                # Add entry to database
                success = db.add_entry(
                    license_plate=license_plate or "",
                    detail_type=detail_type,
                    advisor=advisor or "",
                    location=location,
                    hours=hours,
                    entry_date=str(entry_date),
                    notes=notes
                )
                
                if success:
                    show_success_message(f"Entry added successfully for {(license_plate or '').upper()}")
                    # Clear notes after successful submission
                    st.session_state.current_notes = ""
                    st.balloons()
                else:
                    show_error_message("Failed to add entry. Please try again.")
        
        if cancel:
            # Clear notes on cancel
            st.session_state.current_notes = ""

def show_dashboard_page(db):
    st.header("Dashboard Overview")
    
    # Get summary statistics
    stats = db.get_summary_stats()
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Entries",
            value=stats['total_entries']
        )
    
    with col2:
        st.metric(
            label="Total Hours",
            value=f"{stats['total_hours']}h"
        )
    
    with col3:
        st.metric(
            label="Today's Entries",
            value=stats['today_entries']
        )
    
    with col4:
        st.metric(
            label="Today's Hours",
            value=f"{stats['today_hours']}h"
        )
    
    st.divider()
    
    # Recent activity
    st.subheader("Recent Activity")
    recent_entries = db.get_recent_entries(limit=10)
    
    if recent_entries:
        df = convert_entries_to_dataframe(recent_entries)
        
        # Display without ID column for cleaner view
        display_df = df.drop('ID', axis=1)
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No entries found. Add your first detailing entry to get started!")

def show_view_entries_page(db):
    st.header("📋 Complete Detail Log")
    
    # Filter controls (matching wireframe)
    col1, col2 = st.columns(2)
    
    with col1:
        detailer_filter = st.selectbox(
            "Filter by Detailer:",
            ["All Detailers", "John Smith", "Maria Garcia", "David Chen"],
            help="Filter entries by specific detailer"
        )
    
    with col2:
        date_filter = st.selectbox(
            "Date Range:",
            ["Last 30 Days", "This Week", "This Month", "All Time"],
            help="Filter entries by date range"
        )
    
    # Search box
    search_term = st.text_input(
        "🔍 Search by license plate, stock #, or notes...",
        placeholder="Enter search term",
        help="Search through all entries"
    )
    
    # Controls row
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        limit = st.selectbox("Show entries:", [25, 50, 100, 250], index=1)
    
    with col2:
        sort_order = st.selectbox("Sort by:", ["Newest First", "Oldest First"])
    
    with col3:
        refresh = st.button("🔄 Refresh", use_container_width=True)
    
    # Get entries
    entries = db.get_recent_entries(limit=limit)
    
    if sort_order == "Oldest First":
        entries = list(reversed(entries))
    
    # Apply search filter if provided
    if search_term:
        filtered_entries = []
        search_lower = search_term.lower()
        for entry in entries:
            if (search_lower in entry['license_plate'].lower() or
                search_lower in entry['detail_type'].lower() or
                search_lower in entry['advisor'].lower() or
                (entry['notes'] and search_lower in entry['notes'].lower())):
                filtered_entries.append(entry)
        entries = filtered_entries
    
    if entries:
        # Summary stats (matching wireframe style)
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
        
        # Entry list with better styling
        for i, entry in enumerate(entries):
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
        col1, col2 = st.columns(2)
        
        with col1:
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
        
        with col2:
            st.markdown(f"**Showing {len(entries)} entries**")
    else:
        st.info("No entries found. Add your first detailing entry to get started!")

def show_edit_form(db, entry_id):
    st.subheader("Edit Entry")
    
    # Get current entry data
    entries = db.get_recent_entries(limit=1000)  # Get all to find the specific one
    current_entry = None
    
    for entry in entries:
        if entry['id'] == entry_id:
            current_entry = entry
            break
    
    if not current_entry:
        show_error_message("Entry not found")
        del st.session_state.edit_entry_id
        st.rerun()
        return
    
    with st.form("edit_entry_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            license_plate = st.text_input(
                "License Plate *",
                value=current_entry['license_plate']
            )
            
            detail_type = st.selectbox(
                "Detail Type *",
                options=get_detail_types(),
                index=get_detail_types().index(current_entry['detail_type'])
            )
            
            advisor = st.text_input(
                "Advisor Name *",
                value=current_entry['advisor']
            )
        
        with col2:
            location = st.selectbox(
                "Work Location *",
                options=get_locations(),
                index=get_locations().index(current_entry['location'])
            )
            
            hours = st.number_input(
                "Hours *",
                min_value=0.0,
                max_value=24.0,
                step=0.25,
                value=float(current_entry['hours'])
            )
            
            entry_date = st.date_input(
                "Service Date *",
                value=datetime.strptime(current_entry['entry_date'], '%Y-%m-%d').date()
            )
        
        notes = st.text_area(
            "Notes (Optional)",
            value=current_entry['notes'] or ""
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            submitted = st.form_submit_button("💾 Save Changes", use_container_width=True)
        
        with col2:
            cancelled = st.form_submit_button("❌ Cancel", use_container_width=True)
        
        if submitted:
            errors = validate_form_data(license_plate, detail_type, advisor, location, hours)
            
            if errors:
                for error in errors:
                    show_error_message(error)
            else:
                success = db.update_entry(
                    entry_id=entry_id,
                    license_plate=license_plate,
                    detail_type=detail_type,
                    advisor=advisor,
                    location=location,
                    hours=hours,
                    entry_date=str(entry_date),
                    notes=notes
                )
                
                if success:
                    show_success_message("Entry updated successfully")
                    del st.session_state.edit_entry_id
                    st.rerun()
                else:
                    show_error_message("Failed to update entry")
        
        if cancelled:
            del st.session_state.edit_entry_id
            st.rerun()

def show_search_filter_page(db):
    st.header("Search & Filter Entries")
    
    # Search and filter controls
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Search by License Plate")
        search_plate = st.text_input("Enter license plate:", placeholder="ABC-1234")
        
        if st.button("🔍 Search", use_container_width=True) and search_plate:
            entries = db.get_entries_by_license_plate(search_plate)
            
            if entries:
                st.success(f"Found {len(entries)} entries for {search_plate.upper()}")
                df = convert_entries_to_dataframe(entries)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.warning(f"No entries found for {search_plate.upper()}")
    
    with col2:
        st.subheader("Filter by Date Range")
        date_range_option = st.selectbox(
            "Select date range:",
            list(get_date_range_options().keys())
        )
        
        date_ranges = get_date_range_options()
        
        if date_range_option == "Custom Range":
            col2a, col2b = st.columns(2)
            with col2a:
                start_date = st.date_input("Start Date:", value=date.today() - timedelta(days=7))
            with col2b:
                end_date = st.date_input("End Date:", value=date.today())
        else:
            start_date, end_date = date_ranges[date_range_option]
        
        if st.button("📅 Filter by Date", use_container_width=True):
            entries = db.get_entries_by_date_range(str(start_date), str(end_date))
            
            if entries:
                st.success(f"Found {len(entries)} entries from {start_date} to {end_date}")
                df = convert_entries_to_dataframe(entries)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Quick stats for filtered data
                stats = calculate_duration_stats(entries)
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Entries", len(entries))
                with col2:
                    st.metric("Total Hours", f"{stats['total']:.1f}h")
                with col3:
                    st.metric("Average Hours", f"{stats['avg']:.1f}h")
            else:
                st.warning(f"No entries found from {start_date} to {end_date}")

def show_reports_page(db):
    st.header("Reports & Analytics")
    
    # Date range selector for reports
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
            
            # Detail type breakdown
            st.subheader("Detail Type Breakdown")
            detail_type_counts = df['Detail Type'].value_counts()
            st.bar_chart(detail_type_counts)
            
            # Advisor performance
            st.subheader("Advisor Performance")
            advisor_stats = get_advisor_stats(entries)
            
            if advisor_stats:
                advisor_df = pd.DataFrame.from_dict(advisor_stats, orient='index')
                advisor_df = advisor_df.round(2)
                st.dataframe(advisor_df, use_container_width=True)
            
            # Location usage
            st.subheader("Location Usage")
            location_counts = df['Location'].value_counts()
            st.bar_chart(location_counts)
            
            # Export report
            st.subheader("Export Report")
            csv_data = export_to_csv(df, f"detailing_report_{report_start}_{report_end}.csv")
            
            st.download_button(
                label="📥 Download Report as CSV",
                data=csv_data,
                file_name=f"detailing_report_{report_start}_{report_end}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.warning(f"No entries found for the selected date range ({report_start} to {report_end})")

if __name__ == "__main__":
    main()
