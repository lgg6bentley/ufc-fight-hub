import os
import sqlite3
from flask import Flask, render_template, request, url_for, redirect
import numpy as np

# --- CONFIGURATION ---
app = Flask(__name__)
# The database path should match the one used in db.py
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fighters.db')


# --- DATABASE UTILITIES ---

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn

def get_all_fighters():
    """Fetches all fighter stats from the database."""
    conn = get_db_connection()
    # Order by name for a cleaner roster display
    fighters = conn.execute("SELECT * FROM fighter_stats ORDER BY name").fetchall()
    conn.close()
    return [dict(f) for f in fighters]

def get_fighter_by_name(name):
    """Fetches a single fighter's data by name."""
    clean_name = name.strip()
    conn = get_db_connection()
    # Using 'COLLATE NOCASE' can help with case sensitivity in lookups
    fighter = conn.execute(
        """
        SELECT * FROM fighter_stats WHERE name = ? COLLATE NOCASE
        """, (clean_name,)
    ).fetchone()
    conn.close()
    return dict(fighter) if fighter else None

def get_finish_history(fighter_name):
    """Fetches fight history for a given fighter where they won."""
    conn = get_db_connection()
    history = conn.execute(
        """
        SELECT finish_method, fight_date FROM fight_history 
        WHERE winner_name = ? COLLATE NOCASE ORDER BY fight_date DESC
        """, (fighter_name.strip(),)
    ).fetchall()
    conn.close()
    return [dict(h) for h in history]


# --- DATA PROCESSING & PREDICTION CORE ---

# Feature vector names used for prediction calculation
FEATURE_VECTOR = [
    'height_in', 'age', 'reach_in', 'sig_str_lpm', 
    'sig_str_acc_pct', 'td_avg', 'td_acc_pct', 'sub_avg'
]

# Weights for each feature (these are arbitrary for demonstration)
FEATURE_WEIGHTS = np.array([
    0.05,  # height_in (small)
    0.05,  # age (small)
    0.10,  # reach_in (medium)
    0.15,  # sig_str_lpm (high)
    0.15,  # sig_str_acc_pct (high)
    0.15,  # td_avg (high)
    0.15,  # td_acc_pct (high)
    0.20   # sub_avg (highest for grappling specialists)
])

# Max/Min values for normalization (based on estimated typical ranges)
# NOTE: In a real model, these would be calculated from a large dataset.
MAX_VALUES = np.array([
    80,    # height_in
    45,    # age
    85,    # reach_in
    10.0,  # sig_str_lpm
    70.0,  # sig_str_acc_pct
    10.0,  # td_avg
    100.0, # td_acc_pct
    5.0    # sub_avg
])
MIN_VALUES = np.array([
    60,    # height_in
    20,    # age
    60,    # reach_in
    1.0,   # sig_str_lpm
    20.0,  # sig_str_acc_pct
    0.0,   # td_avg
    0.0,   # td_acc_pct
    0.0    # sub_avg
])


def normalize_data(data):
    """Normalizes fighter data based on global MIN/MAX values."""
    vector = np.array([data[feat] for feat in FEATURE_VECTOR])
    # Apply Min-Max normalization
    normalized_vector = (vector - MIN_VALUES) / (MAX_VALUES - MIN_VALUES)
    # Clamp values between 0 and 1 to prevent extremes
    return np.clip(normalized_vector, 0, 1)

def calculate_feature_diff(f1_data, f2_data):
    """Calculates the weighted difference score between two fighters (A - B)."""
    # 1. Normalize data for both fighters
    f1_norm = normalize_data(f1_data)
    f2_norm = normalize_data(f2_data)

    # 2. Calculate the difference (Fighter 1 - Fighter 2)
    diff_vector = f1_norm - f2_norm

    # 3. Apply weights and sum the result
    weighted_diff_score = np.dot(diff_vector, FEATURE_WEIGHTS)

    return weighted_diff_score

def calculate_finish_score(fighter_name):
    """Calculates a bonus score based on recent finishing history."""
    history = get_finish_history(fighter_name)
    score = 0
    # Simple scoring: more recent finishes get a higher score
    for i, fight in enumerate(history[:5]): # Only look at last 5 wins
        if fight['finish_method'] in ['KO/TKO', 'Submission']:
            # Assign weight inversely proportional to recency (index)
            score += (5 - i) * 0.015  
    return score

def predict_win_rate(f1_data, f2_data):
    """
    Combines feature difference and finish score to get a final win probability.
    Returns: (win_rate_a, win_rate_b)
    """
    
    # 1. Calculate the core feature difference score
    feature_score = calculate_feature_diff(f1_data, f2_data)
    
    # 2. Calculate finish bonus scores
    finish_a = calculate_finish_score(f1_data['name'])
    finish_b = calculate_finish_score(f2_data['name'])
    
    # 3. Adjust the feature score by the finish score difference
    final_score = feature_score + (finish_a - finish_b)

    # 4. Map the score to a probability (using a sigmoid-like function)
    # The score ranges from approx -1.0 to 1.0. 
    # We map it to [0, 1] probability. 
    # score=0 -> 50% chance. score=1 -> ~85% chance.
    probability_a = 1.0 / (1.0 + np.exp(-final_score * 2.5))
    
    win_rate_a = round(probability_a * 100, 1)
    win_rate_b = round(100.0 - win_rate_a, 1)
    
    return win_rate_a, win_rate_b

def get_fighter_data_for_display(fighter_data):
    """Formats fighter data for presentation in the Tale of the Tape."""
    if not fighter_data:
        return {}
        
    # Calculate record string
    record_str = f"{fighter_data['record_wins']}-{fighter_data['record_losses']}"

    # Prepare data dictionary
    display_data = {
        'name': fighter_data['name'],
        'record': record_str,
        # Use existing keys for the template loop
        'height_in': fighter_data['height_in'],
        'age': fighter_data['age'],
        'reach_in': fighter_data['reach_in'],
        'sig_str_lpm': fighter_data['sig_str_lpm'],
        'sig_str_acc_pct': fighter_data['sig_str_acc_pct'],
        'td_avg': fighter_data['td_avg'],
        'td_acc_pct': fighter_data['td_acc_pct'],
        'sub_avg': fighter_data['sub_avg'],
        'ko_win_pct': fighter_data['ko_win_pct'],
        'sub_win_pct': fighter_data['sub_win_pct'],
    }
    return display_data

def format_fighter_record(fighter_data):
    """Formats fighter data for the roster display (fighters.html)."""
    return {
        'name': fighter_data['name'],
        # Format record as "W-L" string
        'record': f"{fighter_data['record_wins']}-{fighter_data['record_losses']}", 
        'age': fighter_data['age'],
        'stance': fighter_data['stance'],
    }


# --- FLASK ROUTES ---

@app.route('/')
def index():
    """Home page route."""
    return render_template('index.html')

@app.route('/fighters')
def fighters_page():
    """Route to display all fighter stats in a roster table."""
    
    # 1. Fetch raw data from the database
    raw_fighters = get_all_fighters()
    
    # 2. Format the data for the template using the new utility
    all_fighters_data = [format_fighter_record(f) for f in raw_fighters]
    
    # 3. Render the template and pass the data
    return render_template('fighters.html', all_fighters=all_fighters_data)

@app.route('/prediction', methods=['GET', 'POST'])
def prediction_page():
    """Route for the prediction simulator."""
    
    # Set default structure for the template
    prediction_result = {
        'fighter_a': request.args.get('f1', ''), # Pre-fill from roster link
        'fighter_b': request.args.get('f2', ''), # NEW: Pre-fill fighter B from Upcoming page link
        'error': None,
        'win_rate_a': 50.0,
        'win_rate_b': 50.0,
        'stats_a': {}, 
        'stats_b': {}
    }

    if request.method == 'POST':
        # 1. Get fighter names from the form
        f1_name = request.form.get('fighter_a_name', '').strip()
        f2_name = request.form.get('fighter_b_name', '').strip()
        
        prediction_result['fighter_a'] = f1_name
        prediction_result['fighter_b'] = f2_name

        # 2. Fetch data
        f1_data = get_fighter_by_name(f1_name)
        f2_data = get_fighter_by_name(f2_name)

        # 3. Check for errors (fighter not found)
        if not f1_data or not f2_data:
            not_found = []
            if not f1_data:
                not_found.append(f"'{f1_name}'")
            if not f2_data:
                not_found.append(f"'{f2_name}'")
                
            prediction_result['error'] = (
                f"One or both fighters ({' or '.join(not_found)}) were not found in the database. "
                f"Please check spelling."
            )
            # Render the template with the error, retaining the input names
            return render_template('prediction.html', prediction_result=prediction_result)

        # 4. Run prediction
        win_rate_a, win_rate_b = predict_win_rate(f1_data, f2_data)
        
        # 5. Format all data for the template
        prediction_result['win_rate_a'] = win_rate_a
        prediction_result['win_rate_b'] = win_rate_b
        
        # Use the correct keys 'stats_a' and 'stats_b' to match the template
        prediction_result['stats_a'] = get_fighter_data_for_display(f1_data)
        prediction_result['stats_b'] = get_fighter_data_for_display(f2_data)

    elif request.method == 'GET':
        # If the user comes from the roster link or upcoming page, pre-fill fighters
        if prediction_result['fighter_a'] and prediction_result['fighter_b']:
            # Handle pre-filling both fighters from the Upcoming link
            f1_data = get_fighter_by_name(prediction_result['fighter_a'])
            f2_data = get_fighter_by_name(prediction_result['fighter_b'])

            if f1_data and f2_data:
                 # Run prediction immediately when both are pre-filled
                win_rate_a, win_rate_b = predict_win_rate(f1_data, f2_data)
                prediction_result['win_rate_a'] = win_rate_a
                prediction_result['win_rate_b'] = win_rate_b
                prediction_result['stats_a'] = get_fighter_data_for_display(f1_data)
                prediction_result['stats_b'] = get_fighter_data_for_display(f2_data)
            elif f1_data:
                 # Handle case where only Fighter A is pre-filled (from roster)
                 prediction_result['stats_a'] = get_fighter_data_for_display(f1_data)
        elif prediction_result['fighter_a']:
            # Handle case where only Fighter A is pre-filled (from roster)
            f1_data = get_fighter_by_name(prediction_result['fighter_a'])
            if f1_data:
                prediction_result['stats_a'] = get_fighter_data_for_display(f1_data)
                
    
    return render_template('prediction.html', prediction_result=prediction_result)

@app.route('/upcoming')
def upcoming_page():
    """Route to display the upcoming fight card."""
    # This route just needs to render the template since the data is defined in upcoming.html
    return render_template('upcoming.html')

if __name__ == '__main__':
    # Ensure the database is initialized before starting the app
    try:
        if not os.path.exists(DB_PATH):
            print(f"WARNING: Database file not found at {DB_PATH}. Please run db.py first.")
    except Exception as e:
        print(f"Error checking DB path: {e}")
        
    app.run(debug=True)
    