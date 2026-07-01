import json
import pandas as pd
import os
import glob
import numpy as np
from datetime import datetime

RAW_DIR = os.path.expanduser("~/vessel_thesis_data/port_raw_json")
WEATHER_FILE = os.path.expanduser("~/vessel_thesis_data/port_weather_history.csv")
OUTPUT_FILE = os.path.expanduser("~/vessel_thesis_data/FINAL_COMPLETED_DATASET.csv")

PORTS = {
    "Rotterdam": [[51.841658, 3.773705], [52.157934, 4.566869]],
    "Antwerp": [[51.148642, 3.991113], [51.425767, 4.629284]],  
    "Bremerhaven": [[53.405569, 8.319574], [53.742869, 8.826447]],
    "Hamburg": [[53.42139, 9.420447], [53.766115, 10.213034]],
    "Felixstowe": [[51.8936, 1.204559], [52.00323, 1.405326]],
    "Singapore": [[1.134113, 103.590426], [1.478245, 104.169004]],
    "Hong_Kong": [[22.1494, 113.816524], [22.435998, 114.297945]],
    "Busan": [[34.937053, 128.745516], [35.314085, 129.296829]],
    "Le_Havre": [[49.409881, 0.006354], [49.543037, 0.318253]],
    "Los_Angeles": [[33.631552, -118.337227], [33.804615, -118.165661]],
    "Genoa": [[44.305057, 8.747504], [44.437148, 8.972321]],
    "Piraeus": [[37.913436, 23.604858], [37.95122, 23.646325]],   
    "New_York": [[40.471024, -74.155569], [40.855276, -73.89173]],
    "Savannah": [[31.90103, -81.212774], [32.219065, -80.715808]],
    "Vancouver": [[49.029162, -123.476988], [49.35147, -123.027933]],
    "Melbourne": [[-38.5725, 144.2333], [-37.6254, 145.3349]]
}
def build():
    print("Parsing Raw Data")
    files = glob.glob(os.path.join(RAW_DIR, "*.jsonl"))
    
    ship_specs = {} 
    all_events = [] 

    for f_path in files:
        port_name = os.path.basename(f_path).split('_')[0]
        with open(f_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    meta = data.get('MetaData', {})
                    mmsi = meta.get('MMSI')
                    msg = data.get('Message', {})
                    ts_raw = data.get('mine_timestamp') or meta.get('time_utc')
                    if not mmsi or not ts_raw: continue

                    if 'ShipStaticData' in msg:
                        s = msg['ShipStaticData']
                        dim = s.get('Dimension', {})
                        ship_specs[mmsi] = {
                            "ship_name": meta.get('ShipName', 'Unknown').strip(),
                            "draught": s.get('MaximumStaticDraught', 0),
                            "length": dim.get('A', 0) + dim.get('B', 0),
                            "width": dim.get('C', 0) + dim.get('D', 0),
                            "eta": str(s.get('Eta'))
                        }

                    if 'PositionReport' in msg:
                        status = msg['PositionReport'].get('NavigationalStatus')
                        if status in [0, 1, 5]:
                            all_events.append({
                                "MMSI": mmsi, "Status": status,
                                "Timestamp": ts_raw, "Port": port_name
                            })
                except: continue

    df = pd.DataFrame(all_events)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'].astype(str).str.replace(' UTC', '', regex=False)).dt.tz_localize(None)
    df = df.sort_values(['MMSI', 'Timestamp'])

    # calculate rounded time for all rows
    df['rounded_time'] = df['Timestamp'].dt.round('30min')

    print("Identifying The Completed Journeys")
    df['prev_port'] = df.groupby('MMSI')['Port'].shift(1)
    
    # journey: a ship is moored and the previous port is different
    voyages = df[(df['Status'] == 5) & (df['Port'] != df['prev_port']) & (df['prev_port'].notna())].copy()

    if voyages.empty:
        print("No port-to-port journeys found. Exporting recent port arrivals")
        voyages = df[df['Status'] == 5].drop_duplicates(subset=['MMSI', 'Port'], keep='last').copy()
        voyages['prev_port'] = "Incoming"

    print("Merging Weather and DCI")
    # calculate congestion: ships at anchor per port/time
    congestion = df[df['Status'] == 1].groupby(['Port', 'rounded_time']).size().reset_index(name='Congestion')
    
    # loading the weather
    w_df = pd.read_csv(WEATHER_FILE)
    w_df['timestamp'] = pd.to_datetime(w_df['timestamp']).dt.tz_localize(None)
    w_df = w_df.sort_values('timestamp')

    # merging congestion
    voyages = pd.merge(voyages, congestion, on=['Port', 'rounded_time'], how='left').fillna({'Congestion': 0})
    
    # merging weather
    final_df = pd.merge_asof(
        voyages.sort_values('Timestamp'), 
        w_df.rename(columns={'port_name': 'Port'}),
        left_on='Timestamp', right_on='timestamp', by='Port', direction='nearest'
    )

    print("Finalising Physical Characteristics")
    specs_df = pd.DataFrame.from_dict(ship_specs, orient='index').reset_index().rename(columns={'index': 'MMSI'})
    final_df = final_df.merge(specs_df, on='MMSI', how='left')

    # filtering vessels
    final_df = final_df[final_df['length'] > 50].copy()

    # final columns
    output_cols = {
        'ship_name': 'Ship_Name', 'MMSI': 'MMSI', 'prev_port': 'Origin_Port',
        'Port': 'Destination_Port', 'draught': 'Draught', 'length': 'Length', 
        'width': 'Width', 'Congestion': 'Congestion_Index', 'wind_speed': 'Wind_at_Dest',
        'visibility': 'Visibility_at_Dest', 'Timestamp': 'Arrival_Timestamp', 'eta': 'Crew_Predicted_ETA'
    }
    
    final_df = final_df[list(output_cols.keys())].rename(columns=output_cols)
    final_df.to_csv(OUTPUT_FILE, index=False)
    print(f"Dataset created with {len(final_df)} voyages")

if __name__ == "__main__":
    build()
