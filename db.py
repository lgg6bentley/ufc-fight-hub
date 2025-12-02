import sqlite3
import os

# Define the path to ensure it's created in the project root
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fighters.db')

def setup_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"Creating database tables at: {DB_PATH}")

    # Drop table to ensure a clean start with the new schema
    cursor.execute("DROP TABLE IF EXISTS fighter_stats")

    # Create the main table with NEW style columns (ko_win_pct, sub_win_pct)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fighter_stats (
            name TEXT PRIMARY KEY,
            record_wins INTEGER,
            record_losses INTEGER,
            height_in INTEGER,
            age INTEGER,
            reach_in INTEGER,
            sig_str_lpm REAL,
            sig_str_acc_pct REAL,
            td_avg REAL,
            td_acc_pct REAL,
            sub_avg REAL,
            stance TEXT,
            country TEXT,
            odds REAL,
            ko_win_pct REAL,
            sub_win_pct REAL
        );
    """)

    # --- Full Fighters Data with New Win Percentages (KO/Sub) ---
    # Data Format: (name, wins, losses, height_in, age, reach_in, sig_str_lpm, sig_str_acc_pct, td_avg, td_acc_pct, sub_avg, stance, country, odds, KO_PCT, SUB_PCT)
    fighters_data = [
        ('Merab Dvalishvili', 21, 4, 66, 34, 68, 4.33, 59.45, 6.40, 37.86, 0.27, 'Orthodox', 'Georgia', -600, 15.0, 5.0),
        ('Petr Yan', 19, 5, 67, 32, 67, 5.12, 60.58, 1.58, 48.21, 0.12, 'Switch', 'Russia', 400, 35.0, 0.0),
        ('Alexandre Pantoja', 30, 5, 65, 35, 67, 4.5, 49.0, 1.6, 40.0, 0.7, 'Orthodox', 'Brazil', -210, 25.0, 45.0),
        ('Joshua Van', 15, 2, 67, 24, 70, 4.8, 50.0, 0.0, 0.0, 0.0, 'Orthodox', 'Myanmar', 175, 50.0, 0.0),
        ('Brandon Moreno', 23, 8, 66, 32, 67, 3.5, 41.0, 1.8, 50.0, 0.7, 'Orthodox', 'Mexico', 115, 20.0, 35.0),
        ('Tatsuro Taira', 17, 1, 67, 24, 70, 4.1, 55.0, 2.0, 33.0, 0.5, 'Orthodox', 'Japan', -135, 10.0, 50.0),
        ('Henry Cejudo', 16, 5, 64, 38, 64, 3.8, 41.0, 2.0, 35.0, 0.4, 'Orthodox', 'USA', 235, 30.0, 25.0),
        ('Payton Talbott', 10, 1, 70, 25, 70, 5.5, 50.0, 0.0, 0.0, 0.0, 'Orthodox', 'USA', -290, 70.0, 0.0),
        ('Jan Blachowicz', 29, 11, 73, 42, 78, 3.6, 49.0, 1.0, 50.0, 0.2, 'Orthodox', 'Poland', -125, 30.0, 10.0),
        ('Bogdan Guskov', 18, 3, 73, 33, 76, 4.0, 45.0, 0.0, 0.0, 0.0, 'Orthodox', 'Uzbekistan', 105, 75.0, 5.0),
    ]

    cursor.executemany("""
        INSERT INTO fighter_stats VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, fighters_data)

    conn.commit()
    conn.close()
    print("Database setup complete and test data inserted.")

if __name__ == "__main__":
    setup_database()
    