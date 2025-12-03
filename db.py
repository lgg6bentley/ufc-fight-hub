import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fighters.db')

def check_data_presence():
    """Checks if the fighter_stats table exists and contains data."""
    if not os.path.exists(DB_PATH):
        print("ERROR: fighters.db file not found in the current directory.")
        return

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check table existence and row count
        cursor.execute("SELECT COUNT(*) FROM fighter_stats")
        row_count = cursor.fetchone()[0]
        
        print(f"--- Database Check Results ---")
        print(f"Found fighters.db at: {DB_PATH}")
        print(f"Total rows in 'fighter_stats' table: {row_count}")
        
        if row_count > 0:
            # We also check one of the specific fighter stats
            cursor.execute("SELECT ko_win_pct FROM fighter_stats WHERE name = 'Merab Dvalishvili'")
            merab_ko = cursor.fetchone()[0]
            print(f"Merab Dvalishvili KO Win % found: {merab_ko}")
            print("\n✅ SUCCESS: Data is present and readable! You can now run 'python app.py'")
        else:
            print("\n❌ WARNING: The table is empty (0 rows). You must run 'python db.py' again.")

    except sqlite3.OperationalError as e:
        print(f"\n❌ ERROR: Could not query the database. Table 'fighter_stats' may not exist. Run 'python db.py'. Error: {e}")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    check_data_presence()
    