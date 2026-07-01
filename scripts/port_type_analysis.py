import pandas as pd
import numpy as np
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

TIDAL_RIVER = ["Rotterdam", "Antwerp", "Hamburg", "Savannah"]
COASTAL_OPEN = ["Bremerhaven", "Felixstowe", "Singapore", "Hong Kong", "Busan", 
                "Le Havre", "Los Angeles", "Genoa", "Piraeus", "New York", 
                "Vancouver", "Melbourne"]

def run_analysis():
    print("Starting Port Evaluation")
    
    # Load the Dataset
    df = pd.read_csv("FINAL_COMPLETED_DATASET.csv")
    
    c_dest = 'Destination_Port' if 'Destination_Port' in df.columns else 'Port'
    c_arr = 'Arrival_Time' if 'Arrival_Time' in df.columns else 'Arrival_Timestamp'
    
    # Categorise the ports
    def get_port_type(port):
        if port in TIDAL_RIVER: return "Tidal / River"
        if port in COASTAL_OPEN: return "Coastal / Open Sea"
        return "Other"
    
    df['Port_Type'] = df[c_dest].apply(get_port_type)
    
    # clean the numerical columns
    for col in ['Draught', 'Length', 'Wind', 'Congestion']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(df[col].median())
    
    results = []

    # evaluating each category separately
    for p_type in ["Tidal / River", "Coastal / Open Sea"]:
        subset = df[df['Port_Type'] == p_type].copy()
        
        if len(subset) < 15:
            print(f"Skipping {p_type}: Not enough data for comparison.")
            continue

        # draught, length, wind, and congestion to predict arrival hour
        X = subset[['Draught', 'Length', 'Wind', 'Congestion']]
        y = pd.to_datetime(subset[c_arr]).dt.hour
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        model = RandomForestRegressor(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        mae = mean_absolute_error(y_test, model.predict(X_test))
        
        results.append({
            "Category": p_type,
            "Voyages": len(subset),
            "Prediction MAE (Hours)": round(mae, 2)
        })

    # final table
    report = pd.DataFrame(results)
    print("Port Type Comparison")
    if not report.empty:
        print(report.to_string(index=False))
    else:
        print("Not enough data for a category-level split.")
    print("="*50)
    
    report.to_csv("port_type_results.csv", index=False)

if __name__ == "__main__":
    run_analysis()
