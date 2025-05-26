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
        initial_sidebar_state="expanded"
    )
    
    # Initialize database
    db = init_database()
    
    # Main title
    st.title("🚗 Auto Detailing Time Tracker")
    st.markdown("**Professional detailing workflow management for dealerships**")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["📝 New Entry", "📊 Dashboard", "📋 View Entries", "🔍 Search & Filter", "📈 Reports"]
    )
    
    if page == "📝 New Entry":
        show_new_entry_page(db)
    elif page == "📊 Dashboard":
        show_dashboard_page(db)
    elif page == "📋 View Entries":
        show_view_entries_page(db)
    elif page == "🔍 Search & Filter":
        show_search_filter_page(db)
    elif page == "📈 Reports":
        show_reports_page(db)

def show_new_entry_page(db):
    st.header("Add New Detailing Entry")
    
    # Create form
    with st.form("new_entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            license_plate = st.text_input(
                "License Plate *",
                placeholder="Enter license plate (e.g., ABC-1234)",
                help="Enter the vehicle's license plate number"
            )
            
            detail_type = st.selectbox(
                "Detail Type *",
                options=get_detail_types(),
                help="Select the type of detailing service"
            )
            
            advisor = st.text_input(
                "Advisor Name *",
                placeholder="Enter advisor's name",
                help="Name of the service advisor handling this vehicle"
            )
        
        with col2:
            location = st.selectbox(
                "Work Location *",
                options=get_locations(),
                help="Select where the detailing work will be performed"
            )
            
            hours = st.number_input(
                "Hours *",
                min_value=0.0,
                max_value=24.0,
                step=0.25,
                value=0.0,
                help="Time spent on detailing (in hours)"
            )
            
            entry_date = st.date_input(
                "Service Date *",
                value=date.today(),
                help="Date when the detailing service was performed"
            )
        
        notes = st.text_area(
            "Notes (Optional)",
            placeholder="Any additional notes about the service...",
            help="Optional notes about the detailing service"
        )
        
        submitted = st.form_submit_button("➕ Add Entry", use_container_width=True)
        
        if submitted:
            # Validate form data
            errors = validate_form_data(license_plate, detail_type, advisor, location, hours)
            
            if errors:
                for error in errors:
                    show_error_message(error)
            else:
                # Add entry to database
                success = db.add_entry(
                    license_plate=license_plate,
                    detail_type=detail_type,
                    advisor=advisor,
                    location=location,
                    hours=hours,
                    entry_date=str(entry_date),
                    notes=notes
                )
                
                if success:
                    show_success_message(f"Entry added successfully for {license_plate.upper()}")
                    st.balloons()
                else:
                    show_error_message("Failed to add entry. Please try again.")

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
    st.header("All Detailing Entries")
    
    # Controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        limit = st.selectbox("Show entries:", [25, 50, 100, 250], index=1)
    
    with col2:
        sort_order = st.selectbox("Sort by:", ["Newest First", "Oldest First"])
    
    with col3:
        st.write("")  # Spacer
        refresh = st.button("🔄 Refresh", use_container_width=True)
    
    # Get entries
    entries = db.get_recent_entries(limit=limit)
    
    if sort_order == "Oldest First":
        entries = list(reversed(entries))
    
    if entries:
        df = convert_entries_to_dataframe(entries)
        
        # Display dataframe with selection
        event = st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )
        
        # Handle row selection for editing/deleting
        if event.selection.rows:
            selected_idx = event.selection.rows[0]
            selected_entry = entries[selected_idx]
            
            st.divider()
            st.subheader("Entry Actions")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✏️ Edit Entry", use_container_width=True):
                    st.session_state.edit_entry_id = selected_entry['id']
                    st.rerun()
            
            with col2:
                if st.button("🗑️ Delete Entry", use_container_width=True, type="secondary"):
                    if st.session_state.get('confirm_delete') != selected_entry['id']:
                        st.session_state.confirm_delete = selected_entry['id']
                        st.rerun()
        
        # Handle delete confirmation
        if 'confirm_delete' in st.session_state:
            entry_to_delete = st.session_state.confirm_delete
            st.warning(f"Are you sure you want to delete entry ID {entry_to_delete}?")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Yes, Delete", type="primary"):
                    if db.delete_entry(entry_to_delete):
                        show_success_message("Entry deleted successfully")
                        del st.session_state.confirm_delete
                        st.rerun()
                    else:
                        show_error_message("Failed to delete entry")
            
            with col2:
                if st.button("Cancel"):
                    del st.session_state.confirm_delete
                    st.rerun()
        
        # Handle edit form
        if 'edit_entry_id' in st.session_state:
            show_edit_form(db, st.session_state.edit_entry_id)
        
        # Export functionality
        st.divider()
        st.subheader("Export Data")
        
        if st.button("📥 Download as CSV", use_container_width=True):
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
