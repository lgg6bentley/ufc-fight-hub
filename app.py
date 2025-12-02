import sqlite3
import os
from flask import Flask, render_template, request, url_for, redirect
import numpy as np
from math import exp # Used for sigmoid function

# --- CONFIGURATION ---
app = Flask(__name__)
# Define the path to the database file
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fighters.db')

# --- CUSTOM LOGISTIC REGRESSION WEIGHTS ---
# These weights are manually defined based on perceived importance of features.
# A higher absolute value means the feature difference has a greater impact on the prediction.
# The order MUST match the feature vector created in get_prediction_data.
CUSTOM_WEIGHTS = {
    'intercept': 0.1,  # Bias term
    'weights': np.array([
        -0.01,  # age_diff (Older is slightly worse)
         0.02,  # height_diff
         0.03,  # reach_diff
         0.15,  # sig_str_lpm_diff
         0.20,  # sig_str_acc_diff 
         0.35,  # td_avg_diff 
         0.60,  # td_acc_diff (Very high importance for grappling success)
         0.30,  # sub_avg_diff
         0.45,  # ko_win_pct_diff (High importance for power/striking style)
         0.40   # sub_win_pct_diff (High importance for submission style)
    ])
}

# --- DATABASE UTILITY FUNCTIONS ---

def fetch_fighter_stats(name):
    """Fetches full stat data for a single fighter."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Updated SQL to select ALL columns, including the new win percentages
    cursor.execute("""
        SELECT 
            name, record_wins, record_losses, height_in, age, reach_in, 
            sig_str_lpm, sig_str_acc_pct, td_avg, td_acc_pct, sub_avg, 
            stance, country, odds, ko_win_pct, sub_win_pct
        FROM fighter_stats 
        WHERE name = ?
    """, (name,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            'name': row[0],
            'record': f"{row[1]}-{row[2]}",
            'record_wins': row[1],
            'record_losses': row[2],
            'height_in': row[3],
            'age': row[4],
            'reach_in': row[5],
            'sig_str_lpm': row[6],
            'sig_str_acc_pct': row[7],
            'td_avg': row[8],
            'td_acc_pct': row[9],
            'sub_avg': row[10],
            'stance': row[11],
            'country': row[12],
            'odds': row[13],
            'ko_win_pct': row[14], # New
            'sub_win_pct': row[15] # New
        }
    return None

def get_fighter_data(name):
    """Fetches a fighter's core data for display on Roster/Tale of Tape."""
    stats = fetch_fighter_stats(name)
    if stats:
        # Format the record and stats for cleaner display
        stats['record'] = f"{stats['record_wins']}-{stats['record_losses']}"
        return stats
    return None

def get_prediction_data(f1_data, f2_data):
    """
    Calculates the differential features (F1 - F2) for the prediction model.
    The order of features in the returned array MUST match the order of CUSTOM_WEIGHTS.
    """
    # Calculate differentials (F1 - F2)
    diff_data = {
        'age_diff': f1_data['age'] - f2_data['age'],
        'height_diff': f1_data['height_in'] - f2_data['height_in'],
        'reach_diff': f1_data['reach_in'] - f2_data['reach_in'],
        'sig_str_lpm_diff': f1_data['sig_str_lpm'] - f2_data['sig_str_lpm'],
        'sig_str_acc_diff': f1_data['sig_str_acc_pct'] - f2_data['sig_str_acc_pct'],
        'td_avg_diff': f1_data['td_avg'] - f2_data['td_avg'],
        'td_acc_diff': f1_data['td_acc_pct'] - f2_data['td_acc_pct'],
        'sub_avg_diff': f1_data['sub_avg'] - f2_data['sub_avg'],
        
        # NEW STYLE FEATURES
        'ko_win_pct_diff': f1_data['ko_win_pct'] - f2_data['ko_win_pct'],
        'sub_win_pct_diff': f1_data['sub_win_pct'] - f2_data['sub_win_pct']
    }
    
    # Create the final feature vector (Order MUST match CUSTOM_WEIGHTS['weights'])
    feature_vector = [
        diff_data['age_diff'],
        diff_data['height_diff'],
        diff_data['reach_diff'],
        diff_data['sig_str_lpm_diff'],
        diff_data['sig_str_acc_diff'],
        diff_data['td_avg_diff'],
        diff_data['td_acc_diff'],
        diff_data['sub_avg_diff'],
        diff_data['ko_win_pct_diff'], # New
        diff_data['sub_win_pct_diff'] # New
    ]
    # Reshape for NumPy array compatibility (1 sample, N features)
    return np.array(feature_vector).reshape(1, -1)

# --- NEW MANUAL PREDICTION FUNCTION ---

def predict_winner_manual(X):
    """Predicts winner using hard-coded Logistic Regression weights (Sigmoid function)."""
    
    # 1. Calculate the linear combination (z = b0 + b1*x1 + b2*x2 + ...)
    # X is the array of feature differentials (1, N).
    z = CUSTOM_WEIGHTS['intercept'] + np.dot(X, CUSTOM_WEIGHTS['weights'])
    
    # 2. Apply the sigmoid function: P(F1 Wins) = 1 / (1 + e^(-z))
    # z[0] because z is a 1-element NumPy array
    prob_f1_wins = 1 / (1 + exp(-z[0]))
    
    return prob_f1_wins

# --- FLASK ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fighters')
def fighters_page():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, record_wins, record_losses, age, stance FROM fighter_stats ORDER BY name")
    fighters_raw = cursor.fetchall()
    conn.close()

    all_fighters = []
    for name, wins, losses, age, stance in fighters_raw:
        all_fighters.append({
            'name': name,
            'record': f"{wins}-{losses}",
            'age': age,
            'stance': stance
        })
        
    return render_template('fighters.html', all_fighters=all_fighters)

@app.route('/upcoming')
def upcoming_page():
    # The actual data for the fights is hard-coded in the upcoming.html template for simplicity
    return render_template('upcoming.html')


@app.route('/predict', methods=['GET', 'POST'])
def prediction_page():
    prediction_result = None
    
    # Handle pre-population from Roster or Upcoming links (GET request)
    if request.method == 'GET':
        f1_name = request.args.get('f1')
        f2_name = request.args.get('f2')
        if f1_name or f2_name:
            prediction_result = {'fighter_a': f1_name or '', 'fighter_b': f2_name or ''}
            
    # Handle prediction submission (POST request)
    if request.method == 'POST':
        f1_name = request.form['fighter_a_name']
        f2_name = request.form['fighter_b_name']
        
        f1_data = fetch_fighter_stats(f1_name)
        f2_data = fetch_fighter_stats(f2_name)
        
        prediction_result = {
            'fighter_a': f1_name,
            'fighter_b': f2_name,
            'stats_a': f1_data,
            'stats_b': f2_data,
            'fighter_a_data': get_fighter_data(f1_name), # For display (record)
            'fighter_b_data': get_fighter_data(f2_name), # For display (record)
        }
        
        if not f1_data or not f2_data:
            prediction_result['error'] = "One or both fighters not found in the database. Please check spelling."
        else:
            try:
                # 1. Get the feature differential vector
                X = get_prediction_data(f1_data, f2_data)

                # 2. Run the NEW manual prediction function
                prob_f1_wins = predict_winner_manual(X)
                
                # 3. Calculate percentages
                win_rate_a = round(prob_f1_wins * 100, 2)
                win_rate_b = round((1 - prob_f1_wins) * 100, 2)
                
                prediction_result.update({
                    'win_rate_a': win_rate_a,
                    'win_rate_b': win_rate_b
                })
                
            except Exception as e:
                app.logger.error(f"Prediction failed: {e}")
                prediction_result['error'] = f"Prediction failed due to model error: {e}"

    return render_template('prediction.html', prediction_result=prediction_result)

if __name__ == '__main__':
    # Ensure the database exists and is populated before running the app
    if not os.path.exists(DB_PATH) or os.path.getsize(DB_PATH) < 100:
         print("WARNING: Database is missing or empty. Please run python db.py first.")
    
    app.run(debug=True)
    