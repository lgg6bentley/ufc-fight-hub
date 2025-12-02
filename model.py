import joblib
import os
import pandas as pd
from sklearn.linear_model import LogisticRegression

# Define the path to ensure they are created in the project root
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model.pkl')
COLUMNS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model_columns.pkl')

# Define the required feature columns that your app.py expects
MODEL_FEATURES = [
    'record_wins_diff', 'record_losses_diff', 'height_in_diff', 'c_diff', 
    'reach_in_diff', 'sig_str_lpm_diff', 'sig_str_acc_pct_diff', 
    'td_avg_diff', 'td_acc_pct_diff', 'sub_avg_diff', 'stance_diff_same'
]

def create_dummy_model():
    print("Creating and saving dummy ML model and columns...")
    
    # 1. Create dummy data (10 samples, 11 features)
    data = {}
    for col in MODEL_FEATURES:
        data[col] = [0.1 * i for i in range(10)]
    
    # Target variable (0 or 1)
    df = pd.DataFrame(data)
    df['target'] = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1] 
    
    X = df[MODEL_FEATURES]
    y = df['target']
    
    # 2. Train a simple model
    model = LogisticRegression()
    # Handle the 'c_diff' typo by renaming it to 'age_diff' for training consistency
    # Note: In your actual app.py, you should fix the get_prediction_data to use 'age_diff'
    X = X.rename(columns={'c_diff': 'age_diff'}, errors='ignore')
    model.fit(X, y)
    
    # Correct the feature list to match the naming used in app.py ('age_diff')
    CORRECTED_FEATURES = [
        'record_wins_diff', 'record_losses_diff', 'height_in_diff', 'age_diff', 
        'reach_in_diff', 'sig_str_lpm_diff', 'sig_str_acc_pct_diff', 
        'td_avg_diff', 'td_acc_pct_diff', 'sub_avg_diff', 'stance_diff_same'
    ]
    
    # 3. Save the model and the columns list
    joblib.dump(model, MODEL_PATH)
    joblib.dump(CORRECTED_FEATURES, COLUMNS_PATH)
    
    print(f"Model saved to: {MODEL_PATH}")
    print(f"Columns saved to: {COLUMNS_PATH}")

if __name__ == "__main__":
    # Ensure pandas and scikit-learn are installed: pip install pandas scikit-learn joblib
    create_dummy_model()
    