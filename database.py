import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect("barcode_history.db")
    cursor = conn.cursor()

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS scanned_items (
                   id INTEGER PRIMARY KEY AUTOINCREMENT, 
                   barcode_value TEXT NOT NULL UNIQUE,
                   barcode_type TEXT NOT NULL,
                   user_label TEXT, 
                   scan_time TEXT NOT NULL
                   )
                   """)
    conn.commit()
    conn.close()

def save_scan(barcode_value, barcode_type):
    conn = sqlite3.connect("barcode_history.db")
    cursor = conn.cursor()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        cursor.execute("""
                   INSERT INTO scanned_items (barcode_value, barcode_type, scan_time)
                   VALUES (?, ?, ?)""", (barcode_value, barcode_type, timestamp))
        conn.commit()
    
    except sqlite3.IntegrityError:
        pass # if barcode already exists, then ignore it
    conn.close()

def update_label(barcode_value, label):
    conn = sqlite3.connect("barcode_history.db")
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE scanned_items
        SET user_label = ?
        WHERE barcode_value = ?
        """, (label, barcode_value))
    
    conn.commit()
    conn.close()

def get_all_items():
    conn = sqlite3.connect("barcode_history.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT barcode_value, barcode_type, user_label, scan_time, return_window
        FROM scanned_items
        ORDER BY scan_time DESC
    """)

    items = cursor.fetchall()

    conn.close()
    return items

def migrate_db():
    conn = sqlite3.connect("barcode_history.db")
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(scanned_items)")
    columns = [row[1] for row in cursor.fetchall()]
    if "return_window" not in columns:
        cursor.execute("ALTER TABLE scanned_items ADD " \
        "COLUMN return_window INTEGER DEFAULT 28")
    
    conn.commit()
    conn.close()


def delete_scan(barcode_value):
    conn = sqlite3.connect("barcode_history.db")
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM scanned_items
        WHERE barcode_value = ?
    """, (barcode_value,))

    conn.commit()
    conn.close()