import pandas as pd
import numpy as np
import ast
import os
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

def parse_crew_eta(eta_str, ref_date):
    if pd.isna(eta_str) or eta_str == 'N/A' or eta_str == "": return pd.NaT
    try:
        if '{' in str(eta_str):
            d = ast.literal_eval(eta_str)
            month, day, hour = int(d.get('Month', 0)), int(d.get('Day', 0)), int(d.get('Hour', 0))
        else:
            return pd.to_datetime(eta_str, errors='coerce')
        if month == 0 or day == 0: return pd.NaT
        return pd.Timestamp(year=ref_date.year, month=month, day=day, hour=hour)
    except: return pd.NaT

def run_training():
    df = pd.read_csv("FINAL_COMPLETED_DATASET.csv")
    
    col_port = 'Destination_Port' if 'Destination_Port' in df.columns else 'Port'
    col_eta = 'Crew_ETA' if 'Crew_ETA' in df.columns else 'AIS_Predicted_ETA'
    col_time = 'Arrival_Timestamp' if 'Arrival_Timestamp' in df.columns else 'Arrival_Time'

    # preparing the data
    df['Arrival_DT'] = pd.to_datetime(df[col_time], errors='coerce')
    df['Captain_ETA_DT'] = df.apply(lambda x: parse_crew_eta(x[col_eta], x['Arrival_DT']), axis=1)
    df['Arrival_Delay_Hours'] = (df['Arrival_DT'] - df['Captain_ETA_DT']).dt.total_seconds() / 3600
    
    # ensuring no rows are dropped if there are 0 values
    for col in ['Draught', 'Length', 'Width', 'Wind', 'Visibility', 'Congestion']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').replace(0, np.nan)
            df[col] = df[col].fillna(df[col].median())

    # cleaning
    df_clean = df.dropna(subset=['Arrival_Delay_Hours']).copy()
    
    # 30 days delay to remove errors that are too long
    df_clean = df_clean[df_clean['Arrival_Delay_Hours'].abs() <= 720] 
    
    df_clean['Port_ID'] = df_clean[col_port].astype('category').cat.codes
    df_clean['Origin_ID'] = df_clean['Origin_Port'].astype('category').cat.codes
    df_clean['Arr_Hour'] = df_clean['Arrival_DT'].dt.hour
    
    print(f"Training samples: {len(df_clean)} verified voyages.")

    # defining the features
    features = [
        'Draught', 'Length', 'Width', 'Congestion', 
        'Wind', 'Visibility', 'Port_ID', 'Origin_ID', 'Arr_Hour'
    ]
    
    X = df_clean[features]
    y = df_clean['Arrival_Delay_Hours']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # baseline
    human_mae = y_test.abs().mean()

    # random forest
    print("Training Random Forest")
    rf = RandomForestRegressor(n_estimators=100, random_state=42)
    rf.fit(X_train, y_train)
    rf_preds = rf.predict(X_test)
    rf_mae = mean_absolute_error(y_test, rf_preds)
    rf_r2 = r2_score(y_test, rf_preds)
    rf_importances = pd.Series(rf.feature_importances_, index=features).sort_values(ascending=False)

    # xgboost
    print("Training XGBoost")
    xgb = XGBRegressor(n_estimators=100, learning_rate=0.05, random_state=42)
    xgb.fit(X_train, y_train)
    xgb_preds = xgb.predict(X_test)
    xgb_mae = mean_absolute_error(y_test, xgb_preds)
    xgb_r2 = r2_score(y_test, xgb_preds)
    xgb_importances = pd.Series(xgb.feature_importances_, index=features).sort_values(ascending=False)

    # feature importance
    print("\n" + "="*50)
    print("Individual MOdel Feature Importance")
    print("="*50)
    print("\n[Random Forest]:")
    print(rf_importances)
    print("\n[XGBoost]:")
    print(xgb_importances)

    # final comparison 
    print(f"Final Performance Comparison ({len(df_clean)} Voyages)")
    print(f"{'Model':<20} | {'MAE (Hours)':<12} | {'R2 Score':<10} | {'Gain %':<8}")
    print("-" * 70)
    print(f"{'Human (AIS ETA)':<20} | {round(human_mae, 2):<12} | {'0.0000':<10} | {'0.0%':<8}")
    
    rf_gain = (1 - (rf_mae / human_mae)) * 100
    print(f"{'Random Forest':<20} | {round(rf_mae, 2):<12} | {round(rf_r2, 4):<10} | {round(rf_gain, 1):<8}")
    
    xgb_gain = (1 - (xgb_mae / human_mae)) * 100
    print(f"{'XGBoost':<20} | {round(xgb_mae, 2):<12} | {round(xgb_r2, 4):<10} | {round(xgb_gain, 1):<8}")

if __name__ == "__main__":
    run_training()
