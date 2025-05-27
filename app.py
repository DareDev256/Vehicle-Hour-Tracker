import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
import os
from PIL import Image

def init_db():
    """Initialize SQLite database with proper persistence"""
    # Use absolute path to ensure database persists
    db_path = os.path.abspath('detailing_tracker.db')
    conn = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
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
    
    if not os.path.exists('photos'):
        os.makedirs('photos')
    conn.commit()
    return conn

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

def display_photos(photo_string):
    """Display photos in a grid layout"""
    if not photo_string:
        return
    
    photo_files = photo_string.split(',')
    if not photo_files or photo_files == ['']:
        return
    
    cols = st.columns(min(4, len(photo_files)))
    for i, photo_file in enumerate(photo_files):
        if photo_file and os.path.exists(os.path.join('photos', photo_file)):
            with cols[i % 4]:
                try:
                    image = Image.open(os.path.join('photos', photo_file))
                    st.image(image, caption=f"Photo {i+1}", use_container_width=True)
                except Exception:
                    st.caption(f"📸 Photo {i+1}")

def get_hours_badge(hours):
    """Return appropriate badge and color for hours worked"""
    hours = float(hours)
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
    
    # Enhanced mobile-friendly CSS
    st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
        height: 3rem;
        font-size: 1.1rem;
        border-radius: 0.5rem;
        font-weight: 600;
    }
    .stFileUploader > div {
        border: 2px dashed #cbd5e1;
        border-radius: 0.5rem;
        padding: 2rem;
        text-align: center;
    }
    .stFileUploader:hover > div {
        border-color: #3b82f6;
        background-color: #f8fafc;
    }
    @media (max-width: 768px) {
        .stColumns { gap: 0.5rem; }
        .main .block-container { padding: 1rem; }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Enhanced Header with Navigation
    st.markdown("""
    <div style="background: linear-gradient(135deg, #2563eb 0%, #3b82f6 50%, #1d4ed8 100%); 
                padding: 1.5rem; border-radius: 0.75rem; margin-bottom: 1rem; 
                color: white; text-align: center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
        <h1 style="margin: 0; font-size: 2rem;">🚗 Auto Detailing Tracker</h1>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Professional workflow management for detailing teams</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize database
    if 'db_conn' not in st.session_state:
        st.session_state.db_conn = init_db()
    
    # Initialize navigation state
    if 'current_view' not in st.session_state:
        st.session_state.current_view = 'dashboard'
    
    conn = st.session_state.db_conn
    
    # Persistent Navigation Bar
    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
    
    with nav_col1:
        if st.button("🏠 Dashboard", use_container_width=True, key="nav_dashboard", 
                    type="primary" if st.session_state.current_view == 'dashboard' else "secondary"):
            st.session_state.current_view = 'dashboard'
            st.rerun()
    
    with nav_col2:
        if st.button("📝 New Entry", use_container_width=True, key="nav_new_entry",
                    type="primary" if st.session_state.current_view == 'new_entry' else "secondary"):
            st.session_state.current_view = 'new_entry'
            st.rerun()
    
    with nav_col3:
        if st.button("📋 View Log", use_container_width=True, key="nav_view_log",
                    type="primary" if st.session_state.current_view == 'view_log' else "secondary"):
            st.session_state.current_view = 'view_log'
            st.rerun()
    
    with nav_col4:
        # Export button in navigation
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM entries")
            entry_count = cursor.fetchone()[0]
            
            if entry_count > 0:
                cursor.execute("SELECT * FROM entries ORDER BY entry_date DESC")
                entries = cursor.fetchall()
                data = []
                for entry in entries:
                    data.append({
                        'ID': entry[0], 'License Plate': entry[1], 'Type': entry[2],
                        'Advisor': entry[3], 'Hours': entry[4], 'Date': entry[5],
                        'Notes': entry[6] or '', 'Created': entry[8] if len(entry) > 8 else ''
                    })
                df = pd.DataFrame(data)
                csv = df.to_csv(index=False)
                
                st.download_button(
                    "📊 Export",
                    csv,
                    f"detailing_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv",
                    use_container_width=True,
                    key="nav_export"
                )
            else:
                st.button("📊 Export", disabled=True, use_container_width=True, key="nav_export_disabled")
        except:
            st.button("📊 Export", disabled=True, use_container_width=True, key="nav_export_error")
    
    st.markdown("---")
    
    # Display content based on current view
    if st.session_state.current_view == 'new_entry':
        show_new_entry(conn)
    elif st.session_state.current_view == 'view_log':
        show_log(conn)
    else:
        show_dashboard(conn)

def show_dashboard(conn):
    """Enhanced dashboard with working Quick Actions"""
    cursor = conn.cursor()
    
    # Get stats
    try:
        cursor.execute("SELECT COUNT(*) FROM entries")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COALESCE(SUM(hours), 0) FROM entries")
        total_hours = cursor.fetchone()[0]
        
        today = date.today().strftime('%Y-%m-%d')
        cursor.execute("SELECT COUNT(*) FROM entries WHERE entry_date = ?", (today,))
        today_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COALESCE(SUM(hours), 0) FROM entries WHERE entry_date = ?", (today,))
        today_hours = cursor.fetchone()[0]
    except:
        total = total_hours = today_count = today_hours = 0
    
    # Stats display
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); 
                padding: 1.5rem; border-radius: 0.75rem; border-left: 4px solid #2563eb; 
                margin-bottom: 1.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h3 style="margin: 0 0 1rem 0; color: #374151;">📊 Today's Progress</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 1.5rem; text-align: center;">
            <div>
                <div style="font-size: 2rem; font-weight: bold; color: #2563eb;">{today_count}</div>
                <div style="font-size: 0.875rem; color: #6b7280; font-weight: 500;">Cars Today</div>
            </div>
            <div>
                <div style="font-size: 2rem; font-weight: bold; color: #059669;">{today_hours:.1f}h</div>
                <div style="font-size: 0.875rem; color: #6b7280; font-weight: 500;">Hours Today</div>
            </div>
            <div>
                <div style="font-size: 2rem; font-weight: bold; color: #dc2626;">{total}</div>
                <div style="font-size: 0.875rem; color: #6b7280; font-weight: 500;">Total Entries</div>
            </div>
            <div>
                <div style="font-size: 2rem; font-weight: bold; color: #7c3aed;">{total_hours:.1f}h</div>
                <div style="font-size: 0.875rem; color: #6b7280; font-weight: 500;">Total Hours</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Working Quick Actions
    st.subheader("⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚗 Start New Entry", use_container_width=True, type="primary", key="quick_new"):
            st.session_state.current_view = "new_entry"
            st.success("✅ Redirecting to New Entry!")
            st.rerun()
    
    with col2:
        if st.button("📋 View All Entries", use_container_width=True, key="quick_view"):
            st.session_state.current_view = "view_log"  
            st.success("✅ Redirecting to View Log!")
            st.rerun()
    
    with col3:
        # Export functionality
        try:
            cursor.execute("SELECT * FROM entries ORDER BY entry_date DESC")
            entries = cursor.fetchall()
            if entries:
                # Create basic export
                data = []
                for entry in entries:
                    data.append({
                        'ID': entry[0],
                        'License Plate': entry[1],
                        'Type': entry[2],
                        'Advisor': entry[3],
                        'Hours': entry[4],
                        'Date': entry[5],
                        'Notes': entry[6] or '',
                        'Created': entry[8] if len(entry) > 8 else ''
                    })
                
                df = pd.DataFrame(data)
                csv = df.to_csv(index=False)
                
                st.download_button(
                    "📊 Export Data",
                    csv,
                    f"detailing_entries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv",
                    use_container_width=True,
                    key="quick_export"
                )
            else:
                st.button("📊 No Data to Export", disabled=True, use_container_width=True)
        except Exception as e:
            st.error(f"Export error: {e}")
    
    # Recent entries
    st.subheader("🔄 Recent Entries")
    try:
        cursor.execute("SELECT * FROM entries ORDER BY entry_date DESC, created_at DESC LIMIT 5")
        entries = cursor.fetchall()
        
        if entries:
            for entry in entries:
                # Clean entry display using Streamlit components only
                with st.container():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"### {entry[1]}")
                        st.markdown(f"**{entry[2]}** • {entry[3]}")
                        st.caption(f"📅 {entry[5]}")
                        if len(entry) > 6 and entry[6]:
                            st.markdown(f"*{entry[6][:100]}{'...' if len(entry[6] or '') > 100 else ''}*")
                    
                    with col2:
                        hours_color = "🟢" if float(entry[4]) <= 1 else "🟡" if float(entry[4]) <= 3 else "🟠" if float(entry[4]) <= 6 else "🔴"
                        st.markdown(f"**{hours_color} {entry[4]}h**")
                        st.caption(f"ID: #{entry[0]}")
                    
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
                                else:
                                    with cols[i % 4]:
                                        st.caption(f"📸 Missing")
                    
                    st.divider()
        else:
            st.info("🎯 No entries yet. Add your first detailing entry to get started!")
    except Exception as e:
        st.error(f"Error loading entries: {e}")

def show_new_entry(conn):
    """Enhanced new entry form"""
    st.header("📝 Add New Entry")
    
    # Timer section
    with st.expander("⏱️ Job Timer & Tips", expanded=False):
        col_timer, col_tips = st.columns([1, 2])
        with col_timer:
            if st.button("▶️ Start Timer", use_container_width=True):
                st.session_state.timer_start = datetime.now()
                st.success("Timer started!")
                st.rerun()
            
            if 'timer_start' in st.session_state:
                elapsed = (datetime.now() - st.session_state.timer_start).total_seconds() / 3600
                st.metric("Active Timer", f"{elapsed:.1f}h")
                if st.button("⏹️ Stop Timer", use_container_width=True):
                    del st.session_state.timer_start
                    st.rerun()
        
        with col_tips:
            st.markdown("""
            **📝 Common Notes:** Pet hair removal, Extra polish needed, Heavy cleaning required, Minor touch-up, Leather conditioning, Paint correction
            
            **📸 Photo Tips:** Take before/after shots, document damage, ensure good lighting
            """)
    
    with st.form("new_entry_form", clear_on_submit=True):
        # Vehicle info
        st.markdown("### 🚗 Vehicle Information")
        col1, col2 = st.columns([2, 1])
        with col1:
            license_plate = st.text_input("License Plate / Stock Number *", placeholder="ABC-123")
        with col2:
            detail_type = st.selectbox("Detail Type *", [
                "New Vehicle Delivery", "CPO/Used Vehicle", "Customer Car",
                "Showroom Detail", "Demo Vehicle", "Full Detail",
                "Interior Detail", "Exterior Detail", "Polish & Wax",
                "Basic Wash", "Engine Bay", "Other"
            ])
        
        # Work details
        st.markdown("### 👤 Work Details")
        col3, col4 = st.columns([2, 1])
        with col3:
            advisor = st.text_input("Detailer Name *", placeholder="Enter detailer name")
        with col4:
            # Smart hours with timer
            if 'timer_start' in st.session_state:
                elapsed = (datetime.now() - st.session_state.timer_start).total_seconds() / 3600
                default_hours = round(max(elapsed, 0.1), 1)
            else:
                default_hours = 1.0
            
            hours = st.number_input("Hours Worked *", min_value=0.1, max_value=24.0, step=0.1, value=default_hours)
        
        entry_date = st.date_input("Date *", value=date.today())
        
        # Photo upload
        st.markdown("### 📸 Photo Documentation")
        uploaded_files = st.file_uploader(
            "Upload photos (max 8)",
            type=['jpg', 'jpeg', 'png', 'heic'],
            accept_multiple_files=True,
            help="Drag and drop photos here"
        )
        
        if uploaded_files:
            if len(uploaded_files) > 8:
                st.warning("⚠️ Maximum 8 photos allowed")
                uploaded_files = uploaded_files[:8]
            
            st.success(f"📷 {len(uploaded_files)} photo(s) ready to upload")
            
            cols = st.columns(min(4, len(uploaded_files)))
            for i, uploaded_file in enumerate(uploaded_files):
                with cols[i % 4]:
                    try:
                        image = Image.open(uploaded_file)
                        image.thumbnail((200, 200))
                        st.image(image, caption=f"Photo {i+1}", use_container_width=True)
                    except Exception:
                        st.caption(f"📸 Photo {i+1}")
        
        # Notes
        notes = st.text_area("📝 Notes & Comments", 
                           placeholder="Customer requests, damage notes, special instructions...",
                           height=120)
        
        # Submit
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
                cursor = conn.cursor()
                
                # Insert entry
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
                
                # Success feedback
                badge, color = get_hours_badge(hours)
                st.success("✅ Entry added successfully!")
                st.markdown(f"""
                <div style="background: #f0f9ff; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #2563eb;">
                    <strong>{license_plate.upper()}</strong> • {detail_type} • {advisor} • 
                    <span style="background: {color}; color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem;">
                        {badge} {hours}h
                    </span> • {entry_date}
                    {f' • {len(uploaded_files)} photo(s)' if uploaded_files else ''}
                </div>
                """, unsafe_allow_html=True)
                
                st.balloons()
                
                if 'timer_start' in st.session_state:
                    del st.session_state.timer_start
                
            except Exception as e:
                st.error(f"❌ Error adding entry: {e}")

def show_log(conn):
    """View all entries with photos"""
    st.header("📋 Entry Log")
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM entries ORDER BY entry_date DESC, created_at DESC")
        entries = cursor.fetchall()
        
        if entries:
            # Stats
            total_hours = sum(float(entry[4]) for entry in entries)
            avg_hours = total_hours / len(entries)
            with_photos = sum(1 for entry in entries if len(entry) > 7 and entry[7])
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Entries", len(entries))
            with col2:
                st.metric("Total Hours", f"{total_hours:.1f}h")
            with col3:
                st.metric("Average Hours", f"{avg_hours:.1f}h")
            with col4:
                st.metric("With Photos", with_photos)
            
            st.divider()
            
            # Display entries with clean layout
            for entry in entries:
                badge, color = get_hours_badge(entry[4])
                
                # Clean entry card using Streamlit components
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
                                else:
                                    with cols[i % 4]:
                                        st.caption(f"📸 Missing")
                    
                    st.divider()
            
            # Export
            st.subheader("📊 Export Options")
            data = []
            for entry in entries:
                data.append({
                    'ID': entry[0],
                    'License Plate': entry[1],
                    'Type': entry[2],
                    'Advisor': entry[3],
                    'Hours': entry[4],
                    'Date': entry[5],
                    'Notes': entry[6] or '',
                    'Created': entry[8] if len(entry) > 8 else ''
                })
            
            df = pd.DataFrame(data)
            csv = df.to_csv(index=False)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    "📥 Export All Entries (CSV)",
                    csv,
                    f"detailing_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv",
                    use_container_width=True
                )
            
            with col2:
                if st.button("🗑️ Clear All Entries", use_container_width=True, type="secondary"):
                    st.session_state.confirm_clear = True
                    st.rerun()
        
        # Confirmation dialog outside the try block to access conn properly
        if st.session_state.get('confirm_clear', False):
            st.warning("⚠️ **Are you sure?** This will permanently delete ALL entries and photos!")
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("✅ Yes, Clear All", type="primary"):
                    try:
                        # Clear database
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM entries")
                        conn.commit()
                        
                        # Clear photos directory
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
        else:
            st.info("🎯 No entries found. Add your first detailing entry to get started!")
    except Exception as e:
        st.error(f"Error loading log: {e}")

if __name__ == "__main__":
    main()