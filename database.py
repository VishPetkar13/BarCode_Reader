import sqlite3

def init_db():
    conn = sqlite3.connect("barcode_history.db")
    cursor = conn.cursor()

    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS scanned_items (
                   id INTEGER PRIMARY KEY AUTOINCREMENT, 
                   barcode_value TEXT NOT NULL,
                   barcode_type TEXT NOT NULL,
                   user_label TEXT, 
                   scan_time TEXT NOT NULL
                   )
                   """)
    conn.commit()
    conn.close()