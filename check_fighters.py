import sqlite3
import os

# Path to your fighters.db file
DB_PATH = os.path.join(os.path.dirname(__file__), 'ai_prediction', 'fighters.db')

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT * FROM fighters")
rows = cursor.fetchall()

print(f"Total fighters found: {len(rows)}")
for row in rows:
    print(row)

conn.close()