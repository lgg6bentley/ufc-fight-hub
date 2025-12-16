import joblib
import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier # NEW: Import Random Forest
from sklearn.preprocessing import StandardScaler 
from sklearn.pipeline import Pipeline 
import numpy as np 

# Define the path to ensure they are created in the project root
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model.pkl')
COLUMNS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model_columns.pkl')

# Corrected Feature List (using 'age_diff' for consistency)
CORRECTED_FEATURES = [
    'record_wins_diff', 'record_losses_diff', 'height_in_diff', 'age_diff', 
    'reach_in_diff', 'sig_str_lpm_diff', 'sig_str_acc_pct_diff', 
    'td_avg_diff', 'td_acc_pct_diff', 'sub_avg_diff', 'stance_diff_same'
]

def create_expert_model_random_forest():
    print("Creating and saving ML model using Random Forest (for balanced confidence)...")
    
    # --- 1. Create a Large, Logically Structured Dataset (5,000 samples) ---
    N_SAMPLES = 5000 
    
    data = {}
    
    # Generate varied but centered differences (simulating fight matchups)
    data['record_wins_diff'] = np.random.normal(0, 5, N_SAMPLES) 
    data['record_losses_diff'] = np.random.normal(0, 3, N_SAMPLES)
    data['height_in_diff'] = np.random.normal(0, 2.5, N_SAMPLES) 
    data['age_diff'] = np.random.normal(0, 3.5, N_SAMPLES) 
    data['reach_in_diff'] = np.random.normal(0, 3, N_SAMPLES) 
    data['sig_str_lpm_diff'] = np.random.normal(0, 1.2, N_SAMPLES) 
    data['sig_str_acc_pct_diff'] = np.random.normal(0, 0.08, N_SAMPLES) 
    data['td_avg_diff'] = np.random.normal(0, 0.8, N_SAMPLES) 
    data['td_acc_pct_diff'] = np.random.normal(0, 0.15, N_SAMPLES)
    data['sub_avg_diff'] = np.random.normal(0, 0.3, N_SAMPLES) 

    # Stance difference (50/50 split for same vs. different stance)
    data['stance_diff_same'] = np.random.randint(0, 2, N_SAMPLES) 

    df = pd.DataFrame(data)
    
    # --- 2. LOGICAL TARGET GENERATION (Simulating Expert Outcome) ---
    weights = {
        'record_wins_diff': 1.5, 
        'sig_str_acc_pct_diff': 2.0,
        'td_avg_diff': 1.0,
        'age_diff': -0.5, 
        'stance_diff_same': 0.1, 
    }
    
    strength_score = (
        df['record_wins_diff'] * weights.get('record_wins_diff', 1.0) +
        df['sig_str_acc_pct_diff'] * weights.get('sig_str_acc_pct_diff', 1.0) +
        df['td_avg_diff'] * weights.get('td_avg_diff', 1.0) +
        df['age_diff'] * weights.get('age_diff', 1.0) +
        df['stance_diff_same'] * weights.get('stance_diff_same', 1.0) +
        df['reach_in_diff'] * 0.7 +
        df['height_in_diff'] * 0.3
    )

    df['target'] = np.where(strength_score > 0, 1, 0)
    upset_mask = np.random.rand(N_SAMPLES) < 0.10 
    df['target'] = np.where(upset_mask, 1 - df['target'], df['target'])
    
    X = df[CORRECTED_FEATURES]
    y = df['target']
    
    # --- 3. Train the Model using a Pipeline (Scaler + Random Forest) ---
    pipeline = Pipeline([
        # Random Forest does not strictly require scaling like Logistic Regression does, 
        # but we keep it here as a safety measure for consistency.
        ('scaler', StandardScaler()),
        # Random Forest Classifier is better for balanced probability outputs
        ('rf', RandomForestClassifier(n_estimators=100, random_state=42)) 
    ])
    
    pipeline.fit(X, y)
    
    # --- 4. Save the model and the columns list ---
    joblib.dump(pipeline, MODEL_PATH)
    joblib.dump(CORRECTED_FEATURES, COLUMNS_PATH)
    
    print(f"Model trained on {N_SAMPLES} expert-simulated samples using Random Forest.")
    print(f"Model and Pipeline saved to: {MODEL_PATH}")
    print(f"Columns saved to: {COLUMNS_PATH}")

if __name__ == "__main__":
    # Ensure all dependencies are installed: pip install pandas scikit-learn joblib numpy
    create_expert_model_random_forest()
    