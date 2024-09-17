import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'contract_events.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS events
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  contract_id TEXT,
                  title TEXT,
                  start_date TEXT,
                  end_date TEXT,
                  event_type TEXT)''')
    conn.commit()
    conn.close()

def save_events(events, contract_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for event in events:
        c.execute('''INSERT INTO events (contract_id, title, start_date, end_date, event_type)
                     VALUES (?, ?, ?, ?, ?)''',
                  (contract_id, event['title'], event['start'], event['end'], event['type']))
    conn.commit()
    conn.close()

def get_all_events():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM events")
    events = c.fetchall()
    conn.close()
    return [{'id': e[0], 'contract_id': e[1], 'title': e[2], 'start': e[3], 'end': e[4], 'type': e[5]} for e in events]

# Initialize the database when this module is imported
init_db()