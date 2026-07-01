import requests
import csv
import time
import os
from datetime import datetime

API_KEY = "2a3637d6eb5c709121f80e2acd07aeef" 
BASE_DIR = "/data/s3819779/vessel_thesis/weather_data"
SAVE_PATH = os.path.join(BASE_DIR, "port_weather_history.csv")

PORTS = [
    {"name": "Rotterdam", "lat": 51.94, "lon": 4.14},
    {"name": "Singapore", "lat": 1.27, "lon": 103.76},
    {"name": "Antwerp", "lat": 51.24, "lon": 4.34},
    {"name": "Hamburg", "lat": 53.53, "lon": 9.94},
    {"name": "Hong Kong", "lat": 22.30, "lon": 114.12},
    {"name": "Los Angeles", "lat": 33.72, "lon": -118.26},
    {"name": "Felixstowe", "lat": 51.95, "lon": 1.31},
    {"name": "Bremerhaven", "lat": 53.54, "lon": 8.55},
    {"name": "Le Havre", "lat": 49.48, "lon": 0.12},
    {"name": "Genoa", "lat": 44.40, "lon": 8.92},
    {"name": "Piraeus", "lat": 37.93, "lon": 23.63},
    {"name": "New York", "lat": 40.68, "lon": -74.01},
    {"name": "Savannah", "lat": 31.90, "lon": -81.09},
    {"name": "Vancouver", "lat": 49.30, "lon": -123.13},
    {"name": "Busan", "lat": 35.10, "lon": 129.04},
    {"name": "Melbourne", "lat": -37.84, "lon": 144.93}
]
def get_weather(port):
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={port['lat']}&lon={port['lon']}&appid={API_KEY}&units=metric"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "port_name": port['name'],
                "temp": data['main']['temp'],
                "wind_speed": data['wind']['speed'],
                "visibility": data.get('visibility', 10000),
                "description": data['weather'][0]['description']
            }
        else:
            print(f"  API Error {response.status_code} for {port['name']}")
            return None
    except Exception as e:
        print(f"  Connection Error: {e}")
        return None

def main():
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)
        print(f"Created folder: {BASE_DIR}")

    print(f"Weather Miner Started. Saving to: {SAVE_PATH}")
    
    while True:
        start_time = time.time()
        weather_records = []

        print(f"Starting Cycle at {datetime.now().strftime('%H:%M:%S')} ")
        for port in PORTS:
            record = get_weather(port)
            if record:
                weather_records.append(record)
                print(f"  Fetched {port['name']}")
            time.sleep(0.5)

        if len(weather_records) > 0:
            try:
                file_exists = os.path.isfile(SAVE_PATH)
                keys = weather_records[0].keys()
                with open(SAVE_PATH, 'a', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=keys)
                    if not file_exists:
                        writer.writeheader()
                    writer.writerows(weather_records)
                print(f"Saved {len(weather_records)} records to csv file ")
            except Exception as e:
                print(f"--- Failed to save: {e} ---")
        else:
            print(" No data collected this cycle ")

        print("Sleeping for 30 minutes")
        time.sleep(1800)

if __name__ == "__main__":
    main()
