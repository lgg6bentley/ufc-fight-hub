import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fighters.db')

# --- CONFIGURATION FOR PROVIDED FIGHT DATA ---

# IMPORTANT: Names are standardized to ASCII ('Blachowicz' instead of 'Błachowicz') 
# to ensure users can easily type them into the web form.
FIGHTER_STATS_DATA = [
    # Fighter Name, Wins, Losses, Height (in), Age, Reach (in), SSLPM, SSACC%, TDAVG, TDACC%, SUBAVG, Stance, Country, KO_W_PCT, SUB_W_PCT
    ('Merab Dvalishvili', 21, 4, 66, 34, 68, 4.33, 59.45, 6.40, 37.86, 0.27, 'Orthodox', 'Georgia', 14.2, 9.5),
    ('Petr Yan', 19, 5, 67, 32, 67, 5.12, 60.58, 1.58, 48.21, 0.12, 'Switch', 'Russia', 21.0, 5.3),
    ('Alexandre Pantoja', 30, 5, 65, 35, 67.5, 4.36, 54.61, 2.80, 47.62, 0.98, 'Orthodox', 'Brazil', 16.7, 33.3),
    ('Joshua Van', 15, 2, 65, 24, 65, 8.86, 61.39, 0.85, 63.64, 0.00, 'Orthodox', 'Myanmar', 60.0, 6.7),
    ('Brandon Moreno', 23, 8, 67, 31, 70, 3.96, 49.52, 1.51, 44.29, 0.39, 'Orthodox', 'Mexico', 17.4, 21.7),
    ('Tatsuro Taira', 17, 1, 67, 25, 70, 2.87, 67.41, 3.21, 48.72, 1.69, 'Orthodox', 'Japan', 17.6, 58.8),
    ('Henry Cejudo', 16, 5, 64, 38, 64, 3.82, 54.81, 1.84, 31.25, 0.15, 'Orthodox', 'USA', 31.2, 6.2),
    ('Payton Talbott', 10, 1, 70, 27, 70.5, 6.05, 59.27, 0.24, 25.00, 0.24, 'Switch', 'USA', 80.0, 10.0),
    # NAME CHANGE: 'Jan Błachowicz' -> 'Jan Blachowicz' for easier user input
    ('Jan Blachowicz', 29, 11, 74, 42, 78, 3.44, 57.61, 1.03, 48.72, 0.33, 'Orthodox', 'Poland', 34.5, 27.6),
    ('Bogdan Guskov', 18, 3, 75, 33, 76, 4.17, 63.10, 0.00, 0.00, 1.05, 'Orthodox', 'Uzbekistan', 55.5, 38.8),
]

# 2. Fight History Data (Ensuring the standardized names are used here too)
FIGHT_HISTORY_DATA = [
    # winner, loser, finish_method, fight_date
    ('Merab Dvalishvili', 'C Sandhagen', 'Decision', '2025-10-04'),
    ('Petr Yan', 'M McGhee', 'Decision', '2025-07-26'),
    ('Alexandre Pantoja', 'Kai Kara France', 'Submission', '2022-07-30'),
    ('Joshua Van', 'Brandon Royval', 'Decision', '2025-06-28'),
    ('Brandon Moreno', 'S Erceg', 'Decision', '2025-03-29'),
    ('Tatsuro Taira', 'H Park', 'Submission', '2025-08-2'),
    ('Henry Cejudo', 'D Cruz', 'KO/TKO', '2020-05-09'),
    ('Payton Talbott', 'F Lima', 'Decision', '2025-06-28'),
    # NAME CHANGE: 'Jan Błachowicz' -> 'Jan Blachowicz'
    ('Jan Blachowicz', 'A Rakic', 'KO/TKO', '2022-05-14'),
    ('Bogdan Guskov', 'N Krylov', 'KO/TKO', '2025-07-26'),
]


# --- DATABASE UTILITY FUNCTIONS ---

def create_tables(conn):
    """Creates both fighter_stats and fight_history tables."""
    cursor = conn.cursor()
    
    # 1. fighter_stats (Main prediction features)
    # The DROP TABLE commands ensure you start fresh every time you run db.py
    cursor.execute("""
        DROP TABLE IF EXISTS fighter_stats;
    """)
    cursor.execute("""
        CREATE TABLE fighter_stats (
            name TEXT PRIMARY KEY,
            record_wins INTEGER,
            record_losses INTEGER,
            height_in REAL,
            age INTEGER,
            reach_in REAL,
            sig_str_lpm REAL,
            sig_str_acc_pct REAL,
            td_avg REAL,
            td_acc_pct REAL,
            sub_avg REAL,
            stance TEXT,
            country TEXT,
            odds REAL DEFAULT 0.0,
            ko_win_pct REAL,
            sub_win_pct REAL
        );
    """)
    
    # 2. fight_history (For trait score calculation)
    cursor.execute("""
        DROP TABLE IF EXISTS fight_history;
    """)
    cursor.execute("""
        CREATE TABLE fight_history (
            fight_id INTEGER PRIMARY KEY AUTOINCREMENT,
            winner_name TEXT NOT NULL,
            loser_name TEXT,
            finish_method TEXT NOT NULL, -- 'KO/TKO', 'Submission', 'Decision'
            fight_date TEXT
        );
    """)
    conn.commit()

def populate_data(conn):
    """Inserts the provided fighter stats and fight history data."""
    cursor = conn.cursor()
    
    # Insert Fighter Stats
    print(f"-> Inserting {len(FIGHTER_STATS_DATA)} fighter stats records.")
    cursor.executemany("""
        INSERT INTO fighter_stats VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0.0, ?, ?)
    """, FIGHTER_STATS_DATA)
    
    # Insert Fight History
    print(f"-> Inserting {len(FIGHT_HISTORY_DATA)} fight history records.")
    cursor.executemany("""
        INSERT INTO fight_history (winner_name, loser_name, finish_method, fight_date) 
        VALUES (?, ?, ?, ?)
    """, FIGHT_HISTORY_DATA)
    
    conn.commit()

def check_data_presence():
    """Drops, creates, populates, and then verifies the data."""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        print("--- Initializing Database ---")
        
        # 1. Create and populate tables
        create_tables(conn)
        populate_data(conn)
        
        # 2. Verification
        cursor = conn.cursor()
        
        # Check counts
        cursor.execute("SELECT COUNT(*) FROM fighter_stats")
        stats_row_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM fight_history")
        history_row_count = cursor.fetchone()[0]
        
        print("\n--- Database Check Results ---")
        print(f"Total rows in 'fighter_stats' table: {stats_row_count}")
        print(f"Total rows in 'fight_history' table: {history_row_count}")
        
        # Spot Check the fixed name
        cursor.execute("SELECT name FROM fighter_stats WHERE name = 'Jan Blachowicz'")
        blachowicz_check = cursor.fetchone()
        
        print(f"Spot Check for 'Jan Blachowicz': {blachowicz_check}")
        
        print("\n✅ SUCCESS: Database has been rebuilt and populated with standardized names!")

    except sqlite3.Error as e:
        print(f"\n❌ DATABASE ERROR: {e}")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    check_data_presence()
