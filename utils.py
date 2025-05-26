import pandas as pd
import streamlit as st
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
import re

def validate_license_plate(plate: str) -> bool:
    """Validate license plate format (basic validation)."""
    if not plate or len(plate.strip()) == 0:
        return False
    
    # Remove spaces and convert to uppercase
    plate = plate.strip().upper()
    
    # Basic validation - allow alphanumeric characters and some special chars
    pattern = r'^[A-Z0-9\-\s]{2,10}$'
    return bool(re.match(pattern, plate))

def validate_hours(hours: float) -> bool:
    """Validate hours input."""
    return 0 <= hours <= 24

def validate_advisor_name(name: str) -> bool:
    """Validate advisor name."""
    if not name or len(name.strip()) < 2:
        return False
    
    # Allow letters, spaces, apostrophes, and hyphens
    pattern = r"^[A-Za-z\s'\-]{2,50}$"
    return bool(re.match(pattern, name.strip()))

def format_license_plate(plate: str) -> str:
    """Format license plate consistently."""
    return plate.strip().upper()

def get_detail_types() -> List[str]:
    """Get list of available detail types."""
    return [
        "Full Detail",
        "Interior Detail",
        "Exterior Detail", 
        "Polish & Wax",
        "Basic Wash",
        "Engine Bay",
        "Headlight Restoration",
        "Paint Correction",
        "Ceramic Coating",
        "Quick Detail"
    ]

def get_locations() -> List[str]:
    """Get list of available work locations/bays."""
    return [
        "Bay 1",
        "Bay 2", 
        "Bay 3",
        "Bay 4",
        "Outside Area",
        "Prep Area",
        "Detail Shop"
    ]

def convert_entries_to_dataframe(entries: List) -> pd.DataFrame:
    """Convert database entries to pandas DataFrame for display."""
    if not entries:
        return pd.DataFrame(columns=[
            'ID', 'License Plate', 'Detail Type', 'Advisor', 
            'Location', 'Hours', 'Date', 'Notes'
        ])
    
    data = []
    for entry in entries:
        data.append({
            'ID': entry['id'],
            'License Plate': entry['license_plate'],
            'Detail Type': entry['detail_type'],
            'Advisor': entry['advisor'],
            'Location': entry['location'],
            'Hours': entry['hours'],
            'Date': entry['entry_date'],
            'Notes': entry['notes'] if entry['notes'] else ''
        })
    
    return pd.DataFrame(data)

def format_hours(hours: float) -> str:
    """Format hours for display."""
    if hours == int(hours):
        return f"{int(hours)}h"
    else:
        return f"{hours:.1f}h"

def get_date_range_options() -> Dict[str, Any]:
    """Get predefined date range options."""
    today = date.today()
    
    return {
        "Today": (today, today),
        "Yesterday": (today - timedelta(days=1), today - timedelta(days=1)),
        "Last 7 Days": (today - timedelta(days=6), today),
        "Last 30 Days": (today - timedelta(days=29), today),
        "This Month": (today.replace(day=1), today),
        "Custom Range": None
    }

def export_to_csv(df: pd.DataFrame, filename: str = None) -> str:
    """Convert DataFrame to CSV for download."""
    if filename is None:
        filename = f"detailing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return df.to_csv(index=False)

def show_success_message(message: str):
    """Show a success message with consistent styling."""
    st.success(f"✅ {message}")

def show_error_message(message: str):
    """Show an error message with consistent styling."""
    st.error(f"❌ {message}")

def show_warning_message(message: str):
    """Show a warning message with consistent styling."""
    st.warning(f"⚠️ {message}")

def show_info_message(message: str):
    """Show an info message with consistent styling."""
    st.info(f"ℹ️ {message}")

def calculate_duration_stats(entries: List) -> Dict[str, float]:
    """Calculate duration statistics from entries."""
    if not entries:
        return {'min': 0, 'max': 0, 'avg': 0, 'total': 0}
    
    hours_list = [entry['hours'] for entry in entries]
    
    return {
        'min': min(hours_list),
        'max': max(hours_list),
        'avg': sum(hours_list) / len(hours_list),
        'total': sum(hours_list)
    }

def get_advisor_stats(entries: List) -> Dict[str, Dict]:
    """Get statistics grouped by advisor."""
    advisor_stats = {}
    
    for entry in entries:
        advisor = entry['advisor']
        if advisor not in advisor_stats:
            advisor_stats[advisor] = {
                'entries': 0,
                'total_hours': 0,
                'detail_types': set()
            }
        
        advisor_stats[advisor]['entries'] += 1
        advisor_stats[advisor]['total_hours'] += entry['hours']
        advisor_stats[advisor]['detail_types'].add(entry['detail_type'])
    
    # Convert sets to counts for easier display
    for advisor in advisor_stats:
        advisor_stats[advisor]['unique_detail_types'] = len(advisor_stats[advisor]['detail_types'])
        del advisor_stats[advisor]['detail_types']
    
    return advisor_stats

def format_currency(amount: float, rate_per_hour: float = 0) -> str:
    """Format currency for revenue calculations if rates are provided."""
    if rate_per_hour > 0:
        revenue = amount * rate_per_hour
        return f"${revenue:.2f}"
    return "N/A"

def validate_form_data(license_plate: str, detail_type: str, advisor: str, 
                      location: str, hours: float) -> List[str]:
    """Validate all form data and return list of errors."""
    errors = []
    
    if not validate_license_plate(license_plate):
        errors.append("License plate must be 2-10 characters long and contain only letters, numbers, spaces, and hyphens.")
    
    if not detail_type:
        errors.append("Please select a detail type.")
    
    if not validate_advisor_name(advisor):
        errors.append("Advisor name must be 2-50 characters long and contain only letters, spaces, apostrophes, and hyphens.")
    
    if not location:
        errors.append("Please select a location.")
    
    if not validate_hours(hours):
        errors.append("Hours must be between 0 and 24.")
    
    return errors
