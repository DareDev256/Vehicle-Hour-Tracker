import sqlite3
import os

# Check both databases
for db_name in ['detailing.db', 'detailing_tracker.db']:
    if os.path.exists(db_name):
        print(f"\n=== {db_name} ===")
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM entries")
            count = cursor.fetchone()[0]
            print(f"Entries count: {count}")
            
            if count > 0:
                cursor.execute("SELECT id, license_plate, detail_type, advisor, hours, entry_date FROM entries ORDER BY id DESC LIMIT 3")
                entries = cursor.fetchall()
                print("Recent entries:")
                for entry in entries:
                    print(f"  ID {entry[0]}: {entry[1]} - {entry[2]} - {entry[3]} - {entry[4]}h - {entry[5]}")
        except Exception as e:
            print(f"Error: {e}")
        
        conn.close()