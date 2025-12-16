import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fighters.db')

# --- CONFIGURATION FOR PROVIDED FIGHT DATA ---

FIGHTER_STATS_DATA = [
    # Fighter Name, Wins, Losses, Height (in), Age, Reach (in),
    # SSLPM, SSACC%, TDAVG, TDACC%, SUBAVG, Stance, Country, KO_W_PCT, SUB_W_PCT

    ('Justin Gaethje', 26, 5, 71, 37, 70, 6.59, 59.63, 0.10, 14.29, 0.00, 'Orthodox', 'USA', 70.0, 5.0),
    ('Paddy Pimblett', 23, 3, 70, 30, 73, 5.19, 60.18, 0.96, 28.57, 1.68, 'Orthodox', 'England', 40.0, 30.0),

    ('Kayla Harrison', 19, 1, 68, 34, 69, 4.50, 55.0, 3.20, 50.0, 1.50, 'Orthodox', 'USA', 25.0, 45.0),
    ('Amanda Nunes', 23, 5, 68, 37, 69, 4.40, 51.0, 1.80, 40.0, 0.80, 'Orthodox', 'Brazil', 60.0, 20.0),

    ('Sean O\'Malley', 18, 3, 71, 31, 72, 7.00, 61.0, 0.50, 20.0, 0.20, 'Orthodox', 'USA', 75.0, 10.0),
    ('Song Yadong', 22, 8, 68, 28, 71, 4.80, 57.0, 0.80, 35.0, 0.40, 'Orthodox', 'China', 55.0, 15.0),

    ('Waldo Cortes-Acosta', 16, 2, 75, 31, 78, 3.50, 52.0, 0.20, 15.0, 0.10, 'Orthodox', 'Dominican Republic', 50.0, 10.0),
    ('Derrick Lewis', 29, 12, 75, 40, 79, 2.60, 48.0, 0.10, 10.0, 0.00, 'Orthodox', 'USA', 80.0, 5.0),

    ('Arnold Allen', 20, 3, 70, 31, 72, 3.90, 50.0, 1.20, 30.0, 0.60, 'Orthodox', 'England', 40.0, 25.0),
    ('Joanderson Silva', 16, 3, 70, 28, 72, 4.20, 53.0, 1.00, 28.0, 0.50, 'Orthodox', 'Brazil', 45.0, 20.0),

    ('Natalia Silva', 19, 5, 65, 28, 67, 4.10, 54.0, 1.50, 35.0, 1.20, 'Orthodox', 'Brazil', 35.0, 40.0),
    ('Rose Namajunas', 15, 7, 65, 33, 65, 3.80, 49.0, 1.00, 30.0, 1.00, 'Orthodox', 'USA', 30.0, 35.0),

    ('Umar Nurmagomedov', 19, 1, 70, 29, 69, 4.00, 56.0, 3.00, 55.0, 1.50, 'Orthodox', 'Russia', 25.0, 50.0),
    ('Deiveson Figueiredo', 25, 5, 65, 35, 68, 3.70, 52.0, 1.80, 40.0, 0.90, 'Orthodox', 'Brazil', 45.0, 30.0),
]

FIGHT_HISTORY_DATA = [
    # winner, loser, finish_method, fight_date
    ('Justin Gaethje', 'Paddy Pimblett', 'Decision', '2025-12-15'),
    ('Kayla Harrison', 'Amanda Nunes', 'Submission', '2025-12-15'),
    ('Sean O\'Malley', 'Song Yadong', 'KO/TKO', '2025-12-15'),
    ('Derrick Lewis', 'Waldo Cortes-Acosta', 'KO/TKO', '2025-12-15'),
    ('Arnold Allen', 'Joanderson Silva', 'Decision', '2025-12-15'),
    ('Rose Namajunas', 'Natalia Silva', 'Decision', '2025-12-15'),
    ('Umar Nurmagomedov', 'Deiveson Figueiredo', 'Submission', '2025-12-15'),
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
