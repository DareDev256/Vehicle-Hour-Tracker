import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
import os
from PIL import Image
import base64
import io

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
            photos TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create photos directory if it doesn't exist
    if not os.path.exists('photos'):
        os.makedirs('photos')
    conn.commit()
    return conn

def save_uploaded_photos(uploaded_files, entry_id):
    """Save uploaded photos and return list of filenames"""
    photo_filenames = []
    for i, uploaded_file in enumerate(uploaded_files):
        if uploaded_file is not None:
            # Create unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"entry_{entry_id}_{timestamp}_{i}.{uploaded_file.name.split('.')[-1]}"
            filepath = os.path.join('photos', filename)
            
            # Save the file
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
    
    # Display photos in responsive columns
    cols = st.columns(min(4, len(photo_files)))
    for i, photo_file in enumerate(photo_files):
        if photo_file and os.path.exists(os.path.join('photos', photo_file)):
            with cols[i % 4]:
                try:
                    image = Image.open(os.path.join('photos', photo_file))
                    st.image(image, caption=f"Photo {i+1}", use_column_width=True)
                except Exception:
                    st.caption(f"📸 Photo {i+1} (error loading)")

def get_hours_badge(hours):
    """Return appropriate badge and color for hours worked"""
    hours = float(hours)
    if hours <= 1:
        return "🟢", "#10b981"  # Quick job
    elif hours <= 3:
        return "🟡", "#f59e0b"  # Standard job
    elif hours <= 6:
        return "🟠", "#ea580c"  # Long job
    else:
        return "🔴", "#dc2626"  # Extended job

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
    .stApp {
        padding-top: 1rem;
    }
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    .stButton > button {
        width: 100%;
        height: 3rem;
        font-size: 1.1rem;
        border-radius: 0.5rem;
        font-weight: 600;
    }
    .stSelectbox > div > div {
        font-size: 1rem;
    }
    .stTextInput > div > div > input {
        font-size: 1rem;
        height: 3rem;
    }
    .stTextArea > div > div > textarea {
        font-size: 1rem;
    }
    .stNumberInput > div > div > input {
        font-size: 1rem;
        height: 3rem;
    }
    .stFileUploader > div {
        font-size: 1rem;
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
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.25rem;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 0.75rem 1rem;
            font-size: 1rem;
        }
        .stColumns {
            gap: 0.5rem;
        }
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }
    }
    .hours-badge {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.5rem;
        border-radius: 0.375rem;
        font-size: 0.875rem;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Enhanced header with gradient
    st.markdown("""
    <div style="background: linear-gradient(135deg, #2563eb 0%, #3b82f6 50%, #1d4ed8 100%); 
                padding: 1.5rem; border-radius: 0.75rem; margin-bottom: 2rem; 
                color: white; text-align: center; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
        <h1 style="margin: 0; font-size: 2rem;">🚗 Auto Detailing Tracker</h1>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">Professional workflow management for detailing teams</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize database
    if 'db_conn' not in st.session_state:
        st.session_state.db_conn = init_db()
    
    conn = st.session_state.db_conn
    
    # Initialize active tab state
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = 'dashboard'
    
    # Enhanced navigation with icons
    tab1, tab2, tab3 = st.tabs(["🏠 Dashboard", "📝 New Entry", "📋 View Log"])
    
    # Handle tab switching based on button clicks
    if st.session_state.active_tab == 'new_entry':
        st.session_state.active_tab = 'dashboard'  # Reset after handling
        tab2_selected = True
    elif st.session_state.active_tab == 'view_log':
        st.session_state.active_tab = 'dashboard'  # Reset after handling
        tab3_selected = True
    else:
        tab1_selected = True
    
    with tab1:
        show_dashboard(conn)
    
    with tab2:
        show_new_entry(conn)
    
    with tab3:
        show_log(conn)

def show_dashboard(conn):
    """Enhanced dashboard with mobile-friendly stats"""
    cursor = conn.cursor()
    
    # Get comprehensive stats
    cursor.execute("SELECT COUNT(*) FROM entries")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COALESCE(SUM(hours), 0) FROM entries")
    total_hours = cursor.fetchone()[0]
    
    today = date.today().strftime('%Y-%m-%d')
    cursor.execute("SELECT COUNT(*) FROM entries WHERE entry_date = ?", (today,))
    today_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COALESCE(SUM(hours), 0) FROM entries WHERE entry_date = ?", (today,))
    today_hours = cursor.fetchone()[0]
    
    # Enhanced stats display
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); 
                padding: 1.5rem; border-radius: 0.75rem; border-left: 4px solid #2563eb; 
                margin-bottom: 1.5rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h3 style="margin: 0 0 1rem 0; color: #374151; display: flex; align-items: center;">
            📊 Today's Progress
        </h3>
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
    
    # Quick actions with enhanced buttons
    st.subheader("⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚗 Start New Entry", use_container_width=True, type="primary"):
            st.session_state.active_tab = "new_entry"
            st.rerun()
    
    with col2:
        if st.button("📋 View All Entries", use_container_width=True):
            st.session_state.active_tab = "view_log"
            st.rerun()
    
    with col3:
        # Enhanced export with data check
        cursor.execute("SELECT * FROM entries ORDER BY entry_date DESC")
        entries = cursor.fetchall()
        if entries:
            # Create DataFrame with proper column handling
            df = pd.DataFrame(entries)
            # Handle both old and new schema
            if len(df.columns) == 9:
                df.columns = ['ID', 'License Plate', 'Type', 'Advisor', 'Hours', 'Date', 'Notes', 'Photos', 'Created']
                export_df = df.drop('Photos', axis=1)
            else:
                df.columns = ['ID', 'License Plate', 'Type', 'Advisor', 'Hours', 'Date', 'Notes', 'Created']
                export_df = df
            csv = export_df.to_csv(index=False)
            
            st.download_button(
                "📊 Export Data",
                csv,
                f"detailing_entries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv",
                use_container_width=True
            )
        else:
            st.button("📊 Export Data", disabled=True, use_container_width=True, help="No data to export yet")
    
    # Enhanced recent entries display
    st.subheader("🔄 Recent Entries")
    cursor.execute("SELECT * FROM entries ORDER BY entry_date DESC, created_at DESC LIMIT 5")
    entries = cursor.fetchall()
    
    if entries:
        for entry in entries:
            badge, color = get_hours_badge(entry[4])
            
            # Mobile-friendly entry cards
            with st.container():
                st.markdown(f"""
                <div style="background: white; padding: 1rem; border-radius: 0.5rem; 
                           border: 1px solid #e2e8f0; margin-bottom: 0.75rem;
                           box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                        <div style="flex: 1; min-width: 200px;">
                            <div style="font-weight: 700; font-size: 1.1rem; color: #1f2937; margin-bottom: 0.25rem;">
                                {entry[1]}
                            </div>
                            <div style="color: #6b7280; font-size: 0.9rem; margin-bottom: 0.25rem;">
                                {entry[2]} • {entry[3]}
                            </div>
                            <div style="color: #9ca3af; font-size: 0.8rem;">
                                {entry[5]}
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <span style="background: {color}; color: white; padding: 0.25rem 0.5rem; 
                                        border-radius: 0.375rem; font-weight: 600; font-size: 0.9rem;">
                                {badge} {entry[4]}h
                            </span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Show photos if available
                if entry[7]:  # Photos column
                    display_photos(entry[7])
                    st.markdown("---")
    else:
        st.info("🎯 No entries yet. Add your first detailing entry to get started!")

def show_new_entry(conn):
    """Enhanced new entry form with photo upload and timer"""
    st.header("📝 Add New Entry")
    
    # Enhanced tips and timer section
    with st.expander("💡 Tips & Timer", expanded=False):
        col_tip, col_timer = st.columns([2, 1])
        with col_tip:
            st.markdown("""
            **📝 Common Notes:**
            - Pet hair removal needed
            - Extra polish required
            - Heavy cleaning required  
            - Minor touch-up work
            - Leather conditioning
            - Paint correction
            
            **📸 Photo Tips:**
            - Take before/after shots
            - Document any damage
            - Ensure good lighting
            - Focus on problem areas
            """)
        
        with col_timer:
            st.markdown("**⏱️ Job Timer**")
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
    
    with st.form("new_entry_form"):
        # Vehicle Information
        st.markdown("### 🚗 Vehicle Information")
        col1, col2 = st.columns([2, 1])
        with col1:
            license_plate = st.text_input("License Plate / Stock Number *", placeholder="ABC-123")
        with col2:
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
        
        # Work Information
        st.markdown("### 👤 Work Details")
        col3, col4 = st.columns([2, 1])
        with col3:
            advisor = st.text_input("Detailer Name *", placeholder="Enter detailer name")
        with col4:
            # Smart hours input with timer integration
            if 'timer_start' in st.session_state:
                elapsed = (datetime.now() - st.session_state.timer_start).total_seconds() / 3600
                default_hours = round(max(elapsed, 0.1), 1)
            else:
                default_hours = 1.0
            
            hours = st.number_input("Hours Worked *", min_value=0.1, max_value=24.0, step=0.1, value=default_hours)
        
        entry_date = st.date_input("Date *", value=date.today())
        
        # Photo Upload Section
        st.markdown("### 📸 Photo Documentation")
        st.caption("Upload before/after photos, damage documentation, or progress shots")
        
        uploaded_files = st.file_uploader(
            "Drag and drop photos here, or click to browse",
            type=['jpg', 'jpeg', 'png', 'heic'],
            accept_multiple_files=True,
            help="Maximum 8 photos. Supported formats: JPEG, PNG, HEIC"
        )
        
        # Photo preview
        if uploaded_files:
            if len(uploaded_files) > 8:
                st.warning("⚠️ Maximum 8 photos allowed. Only the first 8 will be saved.")
                uploaded_files = uploaded_files[:8]
            
            st.success(f"📷 {len(uploaded_files)} photo(s) ready to upload")
            
            # Preview grid
            cols = st.columns(min(4, len(uploaded_files)))
            for i, uploaded_file in enumerate(uploaded_files):
                with cols[i % 4]:
                    try:
                        image = Image.open(uploaded_file)
                        image.thumbnail((200, 200))
                        st.image(image, caption=f"Photo {i+1}", use_column_width=True)
                    except Exception:
                        st.caption(f"📸 Photo {i+1}")
        
        # Notes
        st.markdown("### 📝 Notes & Comments")
        notes = st.text_area(
            "Additional details",
            placeholder="Customer requests, damage notes, special instructions, issues encountered...",
            height=120,
            label_visibility="collapsed"
        )
        
        # Submit section
        st.markdown("---")
        col_submit, col_timer_action = st.columns([3, 1])
        
        with col_submit:
            submitted = st.form_submit_button("✅ Add Entry", type="primary", use_container_width=True)
        
        with col_timer_action:
            if 'timer_start' in st.session_state:
                if st.form_submit_button("⏹️ Stop & Submit", use_container_width=True):
                    elapsed = (datetime.now() - st.session_state.timer_start).total_seconds() / 3600
                    hours = round(max(elapsed, 0.1), 1)
                    del st.session_state.timer_start
    
    # Form processing
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
                
                # Insert entry first to get ID
                cursor.execute('''
                    INSERT INTO entries (license_plate, detail_type, advisor, hours, entry_date, notes, photos)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (license_plate.upper().strip(), detail_type, advisor.strip(), hours, str(entry_date), notes.strip(), ''))
                
                entry_id = cursor.lastrowid
                
                # Save photos if any
                photo_string = ''
                if uploaded_files:
                    photo_string = save_uploaded_photos(uploaded_files[:8], entry_id)
                    cursor.execute('UPDATE entries SET photos = ? WHERE id = ?', (photo_string, entry_id))
                
                conn.commit()
                
                # Enhanced success feedback
                badge, color = get_hours_badge(hours)
                st.success("✅ Entry added successfully!")
                st.markdown(f"""
                <div style="background: #f0f9ff; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #2563eb; margin: 1rem 0;">
                    <strong>{license_plate.upper()}</strong> • {detail_type} • {advisor} • 
                    <span style="background: {color}; color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.9rem;">
                        {badge} {hours}h
                    </span> • {entry_date}
                    {f' • {len(uploaded_files)} photo(s)' if uploaded_files else ''}
                </div>
                """, unsafe_allow_html=True)
                
                st.balloons()
                
                # Clear timer if running
                if 'timer_start' in st.session_state:
                    del st.session_state.timer_start
                
                # Auto refresh after success
                import time
                time.sleep(1.5)
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error adding entry: {e}")

def show_log(conn):
    """Enhanced log view with photos and mobile optimization"""
    st.header("📋 Entry Log")
    
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM entries ORDER BY entry_date DESC, created_at DESC")
    entries = cursor.fetchall()
    
    if entries:
        # Enhanced stats
        total_hours = sum(float(entry[4]) for entry in entries)
        avg_hours = total_hours / len(entries) if entries else 0
        
        # Stats cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Entries", len(entries))
        with col2:
            st.metric("Total Hours", f"{total_hours:.1f}h")
        with col3:
            st.metric("Average Hours", f"{avg_hours:.1f}h")
        with col4:
            with_photos = sum(1 for entry in entries if entry[7])
            st.metric("With Photos", with_photos)
        
        st.markdown("---")
        
        # Entries display with enhanced mobile layout
        for entry in entries:
            badge, color = get_hours_badge(entry[4])
            
            with st.container():
                # Enhanced entry card
                st.markdown(f"""
                <div style="background: white; padding: 1.25rem; border-radius: 0.75rem; 
                           border: 1px solid #e2e8f0; margin-bottom: 1rem;
                           box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem;">
                        <div style="flex: 1; min-width: 250px;">
                            <div style="font-weight: 700; font-size: 1.2rem; color: #1f2937; margin-bottom: 0.5rem;">
                                {entry[1]}
                            </div>
                            <div style="color: #374151; font-size: 1rem; margin-bottom: 0.25rem;">
                                <strong>{entry[2]}</strong> • {entry[3]}
                            </div>
                            <div style="color: #6b7280; font-size: 0.9rem; margin-bottom: 0.25rem;">
                                📅 {entry[5]}
                            </div>
                            {f'<div style="color: #4b5563; font-size: 0.9rem; font-style: italic; margin-top: 0.5rem;">"{entry[6][:150]}{"..." if len(entry[6] or "") > 150 else ""}"</div>' if entry[6] else ''}
                        </div>
                        <div style="text-align: right; display: flex; flex-direction: column; align-items: end; gap: 0.5rem;">
                            <span style="background: {color}; color: white; padding: 0.5rem 0.75rem; 
                                        border-radius: 0.5rem; font-weight: 700; font-size: 1rem;">
                                {badge} {entry[4]}h
                            </span>
                            <div style="color: #9ca3af; font-size: 0.8rem;">
                                ID: #{entry[0]}
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Display photos if available
                if entry[7]:  # Photos column
                    st.markdown("**📸 Photos:**")
                    display_photos(entry[7])
                
                st.markdown("---")
        
        # Enhanced export
        st.subheader("📊 Export Options")
        col_export1, col_export2 = st.columns(2)
        
        with col_export1:
            # Basic CSV export with proper column handling
            df = pd.DataFrame(entries)
            if len(df.columns) == 9:
                df.columns = ['ID', 'License Plate', 'Type', 'Advisor', 'Hours', 'Date', 'Notes', 'Photos', 'Created']
                export_df = df.drop('Photos', axis=1)
            else:
                df.columns = ['ID', 'License Plate', 'Type', 'Advisor', 'Hours', 'Date', 'Notes', 'Created']
                export_df = df
            csv = export_df.to_csv(index=False)
            
            st.download_button(
                "📥 Export All Entries (CSV)",
                csv,
                f"detailing_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv",
                use_container_width=True
            )
        
        with col_export2:
            # Summary report
            summary_data = {
                'Total Entries': [len(entries)],
                'Total Hours': [f"{total_hours:.1f}"],
                'Average Hours': [f"{avg_hours:.1f}"],
                'Entries with Photos': [with_photos],
                'Export Date': [datetime.now().strftime('%Y-%m-%d %H:%M')]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_csv = summary_df.to_csv(index=False)
            
            st.download_button(
                "📊 Export Summary Report",
                summary_csv,
                f"detailing_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv",
                use_container_width=True
            )
    else:
        st.info("🎯 No entries found. Add your first detailing entry to get started!")

if __name__ == "__main__":
    main()