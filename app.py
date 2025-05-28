import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
import os
from PIL import Image
import json

def init_db():
    """Initialize SQLite database with persistent storage"""
    db_path = 'detail_log.db'
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute('PRAGMA journal_mode=WAL')
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
            photos TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Auto-cleanup entries older than 60 days
    cursor.execute('''
        DELETE FROM entries 
        WHERE created_at < datetime('now', '-60 days')
    ''')
    
    if not os.path.exists('photos'):
        os.makedirs('photos')
    conn.commit()
    return conn

def delete_entry(conn, entry_id):
    """Delete an entry and its associated photos"""
    cursor = conn.cursor()
    cursor.execute("SELECT photos FROM entries WHERE id = ?", (entry_id,))
    result = cursor.fetchone()
    
    if result and result[0]:
        photo_files = result[0].split(',')
        for photo_file in photo_files:
            if photo_file.strip():
                photo_path = os.path.join('photos', photo_file.strip())
                if os.path.exists(photo_path):
                    os.remove(photo_path)
    
    cursor.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    conn.commit()
    return cursor.rowcount > 0

def get_entry_by_id(conn, entry_id):
    """Get a single entry by ID for editing"""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM entries WHERE id = ?", (entry_id,))
    return cursor.fetchone()

def update_entry(conn, entry_id, license_plate, detail_type, advisor, hours, entry_date, notes):
    """Update an existing entry"""
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE entries 
        SET license_plate = ?, detail_type = ?, advisor = ?, hours = ?, 
            entry_date = ?, notes = ?
        WHERE id = ?
    ''', (license_plate.upper().strip(), detail_type, advisor.strip(), hours, str(entry_date), notes.strip(), entry_id))
    conn.commit()
    return cursor.rowcount > 0

def get_entries_by_date_filter(conn, filter_option):
    """Get entries based on date filter"""
    cursor = conn.cursor()
    
    if filter_option == "Today":
        query = "SELECT * FROM entries WHERE DATE(entry_date) = DATE('now') ORDER BY entry_date DESC, created_at DESC"
    elif filter_option == "Last 7 Days":
        query = "SELECT * FROM entries WHERE entry_date >= DATE('now', '-7 days') ORDER BY entry_date DESC, created_at DESC"
    elif filter_option == "Last 30 Days":
        query = "SELECT * FROM entries WHERE entry_date >= DATE('now', '-30 days') ORDER BY entry_date DESC, created_at DESC"
    elif filter_option == "Last 60 Days":
        query = "SELECT * FROM entries WHERE entry_date >= DATE('now', '-60 days') ORDER BY entry_date DESC, created_at DESC"
    else:  # All
        query = "SELECT * FROM entries ORDER BY entry_date DESC, created_at DESC"
    
    cursor.execute(query)
    return cursor.fetchall()

def save_uploaded_photos(uploaded_files, entry_id):
    """Save uploaded photos and return list of filenames"""
    photo_filenames = []
    for i, uploaded_file in enumerate(uploaded_files):
        if uploaded_file is not None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"entry_{entry_id}_{timestamp}_{i}.{uploaded_file.name.split('.')[-1]}"
            filepath = os.path.join('photos', filename)
            
            with open(filepath, "wb") as f:
                f.write(uploaded_file.getbuffer())
            photo_filenames.append(filename)
    
    return ','.join(photo_filenames)

def get_hours_badge(hours):
    """Return appropriate badge and color for hours worked"""
    if hours <= 1:
        return "🟢", "#10b981"
    elif hours <= 3:
        return "🟡", "#f59e0b"
    elif hours <= 6:
        return "🟠", "#ea580c"
    else:
        return "🔴", "#dc2626"

def main():
    st.set_page_config(
        page_title="Auto Detailing Tracker",
        page_icon="🚗",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Enhanced CSS
    st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
        border-radius: 0.5rem;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.2s;
    }
    .nav-button {
        background: linear-gradient(90deg, #3b82f6, #1d4ed8);
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div style="background: linear-gradient(90deg, #3b82f6, #1d4ed8); padding: 1.5rem; border-radius: 0.75rem; margin-bottom: 2rem;">
        <h1 style="color: white; margin: 0; font-size: 2rem; font-weight: 700;">
            🚗 Auto Detailing Tracker
        </h1>
        <p style="color: #e0f2fe; margin: 0.5rem 0 0 0; font-size: 1.1rem;">
            Professional time tracking and workflow management
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize database
    conn = init_db()
    
    # Navigation
    if 'nav_selection' not in st.session_state:
        st.session_state.nav_selection = "Dashboard"
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Dashboard", use_container_width=True, 
                    type="primary" if st.session_state.nav_selection == "Dashboard" else "secondary"):
            st.session_state.nav_selection = "Dashboard"
            st.rerun()
    
    with col2:
        if st.button("📝 New Entry", use_container_width=True,
                    type="primary" if st.session_state.nav_selection == "New Entry" else "secondary"):
            st.session_state.nav_selection = "New Entry"
            st.rerun()
    
    with col3:
        if st.button("📋 View Log", use_container_width=True,
                    type="primary" if st.session_state.nav_selection == "View Log" else "secondary"):
            st.session_state.nav_selection = "View Log"
            st.rerun()
    
    with col4:
        if st.button("📥 Export", use_container_width=True,
                    type="primary" if st.session_state.nav_selection == "Export" else "secondary"):
            st.session_state.nav_selection = "Export"
            st.rerun()
    
    st.divider()
    
    # Handle delete confirmation
    if 'delete_entry_id' in st.session_state:
        st.warning(f"⚠️ Are you sure you want to delete entry #{st.session_state.delete_entry_id}?")
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("✅ Yes, Delete", type="primary"):
                if delete_entry(conn, st.session_state.delete_entry_id):
                    st.success("🗑️ Entry deleted successfully!")
                else:
                    st.error("❌ Failed to delete entry")
                del st.session_state.delete_entry_id
                st.rerun()
        with col2:
            if st.button("❌ Cancel"):
                del st.session_state.delete_entry_id
                st.rerun()
    
    # Show selected page
    if st.session_state.nav_selection == "Dashboard":
        show_dashboard(conn)
    elif st.session_state.nav_selection == "New Entry":
        show_new_entry(conn)
    elif st.session_state.nav_selection == "View Log":
        show_log(conn)
    elif st.session_state.nav_selection == "Export":
        show_export(conn)

def show_dashboard(conn):
    """Enhanced dashboard with stats and recent entries"""
    st.subheader("📊 Dashboard Overview")
    
    # Quick stats
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), COALESCE(SUM(hours), 0), COALESCE(AVG(hours), 0) FROM entries")
        total_entries, total_hours, avg_hours = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) FROM entries WHERE photos IS NOT NULL AND photos != ''")
        with_photos = cursor.fetchone()[0]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Entries", total_entries)
        with col2:
            st.metric("Total Hours", f"{total_hours:.1f}h")
        with col3:
            st.metric("Average Hours", f"{avg_hours:.1f}h")
        with col4:
            st.metric("With Photos", with_photos)
        
        st.divider()
        
        # Recent entries
        st.subheader("🕒 Recent Entries")
        cursor.execute("SELECT * FROM entries ORDER BY entry_date DESC, created_at DESC LIMIT 5")
        entries = cursor.fetchall()
        
        if entries:
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
                        
                        # Edit and Delete buttons
                        col_edit, col_delete = st.columns(2)
                        with col_edit:
                            if st.button("✏️", key=f"edit_dash_{entry[0]}", help="Edit entry"):
                                st.session_state.edit_entry_id = entry[0]
                                st.session_state.nav_selection = "New Entry"
                                st.rerun()
                        with col_delete:
                            if st.button("🗑️", key=f"delete_dash_{entry[0]}", help="Delete entry"):
                                st.session_state.delete_entry_id = entry[0]
                                st.rerun()
                    
                    # Show photos if available
                    if len(entry) > 7 and entry[7] and entry[7].strip():
                        st.markdown("**📸 Photos:**")
                        photo_files = [f.strip() for f in entry[7].split(',') if f.strip()]
                        
                        if photo_files:
                            cols = st.columns(min(4, len(photo_files)))
                            for i, photo_file in enumerate(photo_files):
                                photo_path = os.path.join('photos', photo_file)
                                if os.path.exists(photo_path):
                                    with cols[i % 4]:
                                        try:
                                            image = Image.open(photo_path)
                                            st.image(image, caption=f"Photo {i+1}", use_container_width=True)
                                        except Exception:
                                            st.caption(f"📸 Photo {i+1}")
                    st.divider()
        else:
            st.info("🎯 No entries yet. Add your first detailing entry to get started!")
    except Exception as e:
        st.error(f"Error loading dashboard: {e}")

def show_new_entry(conn):
    """Enhanced new entry form with edit capability"""
    # Check if we're editing an existing entry
    edit_entry = None
    if 'edit_entry_id' in st.session_state:
        edit_entry = get_entry_by_id(conn, st.session_state.edit_entry_id)
        if edit_entry:
            st.subheader(f"✏️ Edit Entry #{edit_entry[0]}")
        else:
            st.subheader("📝 Add New Detailing Entry")
            del st.session_state.edit_entry_id
    else:
        st.subheader("📝 Add New Detailing Entry")
    
    with st.form("entry_form", clear_on_submit=not edit_entry):
        col1, col2 = st.columns(2)
        
        with col1:
            # License plate
            license_plate = st.text_input("🚗 License Plate", 
                                        value=edit_entry[1] if edit_entry else "",
                                        placeholder="ABC123")
            
            # Detail type
            detail_types = [
                "New Vehicle Delivery",
                "Full Detail",
                "Interior Only",
                "Exterior Only", 
                "Express Wash",
                "Paint Correction",
                "Ceramic Coating",
                "Maintenance Wash"
            ]
            current_index = detail_types.index(edit_entry[2]) if edit_entry and edit_entry[2] in detail_types else 0
            detail_type = st.selectbox("🧽 Detail Type", detail_types, index=current_index)
            
            # Advisor/Detailer
            advisor = st.text_input("👤 Detailer Name",
                                  value=edit_entry[3] if edit_entry else "",
                                  placeholder="Enter detailer name")
        
        with col2:
            # Hours
            hours = st.number_input("⏱️ Hours Worked", 
                                  min_value=0.1, 
                                  max_value=24.0, 
                                  value=float(edit_entry[4]) if edit_entry else 1.0,
                                  step=0.5)
            
            # Date
            entry_date = st.date_input("📅 Service Date", 
                                     value=datetime.strptime(edit_entry[5], '%Y-%m-%d').date() if edit_entry else date.today())
            
            # Photos
            uploaded_files = st.file_uploader("📸 Upload Photos (max 8)", 
                                            accept_multiple_files=True,
                                            type=['jpg', 'jpeg', 'png', 'heic'],
                                            help="Add new photos or replace existing ones")
            
            # Show existing photos for edit mode with delete checkboxes
            replace_photos = False
            photos_to_delete = []
            if edit_entry and len(edit_entry) > 7 and edit_entry[7]:
                st.markdown("**📸 Current Photos:**")
                photo_files = [f.strip() for f in edit_entry[7].split(',') if f.strip()]
                if photo_files:
                    # Display photos with delete checkboxes
                    cols = st.columns(min(3, len(photo_files)))
                    for i, photo_file in enumerate(photo_files):
                        photo_path = os.path.join('photos', photo_file)
                        if os.path.exists(photo_path):
                            with cols[i % 3]:
                                try:
                                    image = Image.open(photo_path)
                                    st.image(image, caption=f"Photo {i+1}", use_container_width=True)
                                except Exception:
                                    st.caption(f"📸 Photo {i+1} (error loading)")
                                
                                # Delete checkbox for each photo
                                if st.checkbox(f"🗑️ Remove Photo {i+1}", 
                                             key=f"delete_photo_{i}_{edit_entry[0]}", 
                                             help=f"Mark Photo {i+1} for deletion"):
                                    photos_to_delete.append(photo_file)
                
                replace_photos = st.checkbox("🔄 Replace all existing photos with new uploads", 
                                           help="Check this to replace current photos, leave unchecked to add to existing photos")
                
                if photos_to_delete:
                    st.warning(f"⚠️ {len(photos_to_delete)} photo(s) marked for deletion. They will be removed when you update the entry.")
                
                st.info("💡 Upload new photos above to add or replace existing ones, or check boxes below photos to mark for deletion")
        
        # Notes
        notes = st.text_area("📝 Notes & Comments", 
                           value=edit_entry[6] if edit_entry and edit_entry[6] else "",
                           placeholder="Customer requests, damage notes, special instructions...",
                           height=120)
        
        # Submit buttons
        if edit_entry:
            col_update, col_cancel = st.columns(2)
            with col_update:
                submitted = st.form_submit_button("✅ Update Entry", type="primary", use_container_width=True)
            with col_cancel:
                cancel_edit = st.form_submit_button("❌ Cancel Edit", use_container_width=True)
                if cancel_edit:
                    del st.session_state.edit_entry_id
                    st.rerun()
        else:
            submitted = st.form_submit_button("✅ Add Entry", type="primary", use_container_width=True)
    
    if submitted:
        if not license_plate or not license_plate.strip():
            st.error("❌ License plate is required")
        elif not advisor or not advisor.strip():
            st.error("❌ Detailer name is required")
        elif hours <= 0:
            st.error("❌ Hours must be greater than 0")
        else:
            try:
                if edit_entry:
                    # Update existing entry
                    if update_entry(conn, edit_entry[0], license_plate, detail_type, advisor, hours, entry_date, notes):
                        cursor = conn.cursor()
                        
                        # Handle photo deletions first
                        if photos_to_delete:
                            for photo_file in photos_to_delete:
                                photo_path = os.path.join('photos', photo_file)
                                if os.path.exists(photo_path):
                                    os.remove(photo_path)
                        
                        # Handle photo updates
                        if replace_photos and uploaded_files:
                            # Delete all existing photos and replace with new ones
                            if edit_entry[7]:
                                old_photo_files = edit_entry[7].split(',')
                                for photo_file in old_photo_files:
                                    if photo_file.strip():
                                        photo_path = os.path.join('photos', photo_file.strip())
                                        if os.path.exists(photo_path):
                                            os.remove(photo_path)
                            
                            # Save new photos
                            new_photo_string = save_uploaded_photos(uploaded_files[:8], edit_entry[0])
                            cursor.execute('UPDATE entries SET photos = ? WHERE id = ?', (new_photo_string, edit_entry[0]))
                        
                        elif uploaded_files or photos_to_delete:
                            # Add new photos or just update after deletions
                            existing_photos = edit_entry[7] if edit_entry[7] else ""
                            current_photos = [p.strip() for p in existing_photos.split(',') if p.strip() and p not in photos_to_delete]
                            
                            # Add new photos if any
                            if uploaded_files:
                                new_photos = save_uploaded_photos(uploaded_files[:8], edit_entry[0])
                                new_photo_list = [p.strip() for p in new_photos.split(',') if p.strip()]
                                current_photos.extend(new_photo_list)
                            
                            # Limit to 8 photos total
                            final_photos = ','.join(current_photos[:8])
                            cursor.execute('UPDATE entries SET photos = ? WHERE id = ?', (final_photos, edit_entry[0]))
                        
                        conn.commit()
                        st.success("✅ Entry and photos updated successfully!")
                        del st.session_state.edit_entry_id
                        st.rerun()
                    else:
                        st.error("❌ Failed to update entry")
                else:
                    # Add new entry
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO entries (license_plate, detail_type, advisor, hours, entry_date, notes, photos)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (license_plate.upper().strip(), detail_type, advisor.strip(), hours, str(entry_date), notes.strip(), ''))
                    
                    entry_id = cursor.lastrowid
                    
                    # Save photos
                    photo_string = ''
                    if uploaded_files:
                        photo_string = save_uploaded_photos(uploaded_files[:8], entry_id)
                        cursor.execute('UPDATE entries SET photos = ? WHERE id = ?', (photo_string, entry_id))
                    
                    conn.commit()
                    
                    badge, color = get_hours_badge(hours)
                    st.success("✅ Entry added successfully!")
                    st.info(f"📊 Entry saved with ID: {entry_id}")
                    
            except Exception as e:
                st.error(f"❌ Error processing entry: {e}")

def show_log(conn):
    """Enhanced log view with date filtering and edit/delete options"""
    st.subheader("📋 View All Entries")
    
    # Date filter
    col1, col2 = st.columns([1, 3])
    with col1:
        date_filter = st.selectbox("📅 Filter by Date", 
                                 ["All", "Today", "Last 7 Days", "Last 30 Days", "Last 60 Days"])
    
    with col2:
        st.info("ℹ️ Entries older than 60 days are automatically archived to maintain performance")
    
    try:
        # Get filtered entries
        entries = get_entries_by_date_filter(conn, date_filter)
        
        if entries:
            # Stats for filtered view
            total_entries = len(entries)
            total_hours = sum(entry[4] for entry in entries)
            with_photos = sum(1 for entry in entries if len(entry) > 7 and entry[7])
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Filtered Entries", total_entries)
            with col2:
                st.metric("Total Hours", f"{total_hours:.1f}h")
            with col3:
                st.metric("Average Hours", f"{total_hours/total_entries:.1f}h")
            with col4:
                st.metric("With Photos", with_photos)
            
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
                            st.markdown(f"*{entry[6][:150]}{'...' if len(entry[6] or '') > 150 else ''}*")
                    
                    with col2:
                        hours_color = "🟢" if float(entry[4]) <= 1 else "🟡" if float(entry[4]) <= 3 else "🟠" if float(entry[4]) <= 6 else "🔴"
                        st.markdown(f"**{hours_color} {entry[4]}h**")
                        st.caption(f"ID: #{entry[0]}")
                        
                        # Edit and Delete buttons
                        col_edit, col_delete = st.columns(2)
                        with col_edit:
                            if st.button("✏️", key=f"edit_log_{entry[0]}", help="Edit entry"):
                                st.session_state.edit_entry_id = entry[0]
                                st.session_state.nav_selection = "New Entry"
                                st.rerun()
                        with col_delete:
                            if st.button("🗑️", key=f"delete_log_{entry[0]}", help="Delete entry"):
                                st.session_state.delete_entry_id = entry[0]
                                st.rerun()
                    
                    # Show photos if available
                    if len(entry) > 7 and entry[7] and entry[7].strip():
                        st.markdown("**📸 Photos:**")
                        photo_files = [f.strip() for f in entry[7].split(',') if f.strip()]
                        
                        if photo_files:
                            cols = st.columns(min(4, len(photo_files)))
                            for i, photo_file in enumerate(photo_files):
                                photo_path = os.path.join('photos', photo_file)
                                if os.path.exists(photo_path):
                                    with cols[i % 4]:
                                        try:
                                            image = Image.open(photo_path)
                                            st.image(image, caption=f"Photo {i+1}", use_container_width=True)
                                        except Exception:
                                            st.caption(f"📸 Photo {i+1}")
                    st.divider()
        else:
            st.info("🎯 No entries found for the selected filter.")
    except Exception as e:
        st.error(f"Error loading entries: {e}")

def show_export(conn):
    """Enhanced export with multiple format options"""
    st.subheader("📥 Export Data")
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM entries ORDER BY entry_date DESC, created_at DESC")
        entries = cursor.fetchall()
        
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
                    'Created At': entry[8] if len(entry) > 8 else ''
                })
            
            df = pd.DataFrame(data)
            
            # Export format selection
            export_format = st.selectbox("📊 Choose Export Format", 
                                       ["CSV", "Excel", "JSON"])
            
            col1, col2 = st.columns(2)
            
            if export_format == "CSV":
                csv = df.to_csv(index=False)
                with col1:
                    st.download_button(
                        "📥 Download CSV",
                        csv,
                        f"detailing_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        "text/csv",
                        use_container_width=True
                    )
            
            elif export_format == "Excel":
                # Create Excel file in memory
                from io import BytesIO
                excel_buffer = BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Detailing Log', index=False)
                excel_buffer.seek(0)
                
                with col1:
                    st.download_button(
                        "📥 Download Excel",
                        excel_buffer.getvalue(),
                        f"detailing_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            
            elif export_format == "JSON":
                json_data = df.to_json(orient='records', indent=2)
                with col1:
                    st.download_button(
                        "📥 Download JSON",
                        json_data,
                        f"detailing_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        "application/json",
                        use_container_width=True
                    )
            
            # Clear all entries option
            with col2:
                if st.button("🗑️ Clear All Entries", use_container_width=True, type="secondary"):
                    st.session_state.confirm_clear = True
                    st.rerun()
            
            # Confirmation dialog for clear all
            if st.session_state.get('confirm_clear', False):
                st.warning("⚠️ **Are you sure?** This will permanently delete ALL entries and photos!")
                col1, col2, col3 = st.columns([1, 1, 1])
                
                with col1:
                    if st.button("✅ Yes, Clear All", type="primary"):
                        try:
                            cursor.execute("DELETE FROM entries")
                            conn.commit()
                            
                            import shutil
                            if os.path.exists('photos'):
                                shutil.rmtree('photos')
                                os.makedirs('photos')
                            
                            st.session_state.confirm_clear = False
                            st.success("🧹 All entries and photos cleared successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error clearing data: {e}")
                
                with col2:
                    if st.button("❌ Cancel"):
                        st.session_state.confirm_clear = False
                        st.rerun()
            
            # Data preview
            st.subheader("📊 Data Preview")
            st.dataframe(df, use_container_width=True)
            
        else:
            st.info("🎯 No entries found. Add your first detailing entry to get started!")
    except Exception as e:
        st.error(f"Error loading export data: {e}")

if __name__ == "__main__":
    main()