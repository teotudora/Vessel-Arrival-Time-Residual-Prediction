import websocket
import json
import os
import time
from datetime import datetime

API_KEY = "c7cc270a20f5546553e9579f67ac7f1199dd0048"
OUT_DIR = os.path.expanduser("~/vessel_thesis_data/port_raw_json")

# 16 bounding boxes
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
    "Genoa": [[44.409881, 8.747504], [44.437148, 8.972321]],
    "Piraeus": [[37.913436, 23.604858], [37.95122, 23.646325]],
    "New_York": [[40.471024, -74.155569], [40.855276, -73.89173]],
    "Savannah": [[31.90103, -81.212774], [32.219065, -80.715808]],
    "Vancouver": [[49.029162, -123.476988], [49.35147, -123.027933]],
    "Melbourne": [[-38.5725, 144.2333], [-37.6254, 145.3349]]
}

ship_registry = {port: {} for port in PORTS}

def on_message(ws, message):
    try:
        # binary to string
        if isinstance(message, bytes):
            message = message.decode('utf-8')
        
        data = json.loads(message)
        meta = data.get('MetaData', {})
        lat = meta.get('latitude')
        lon = meta.get('longitude')
        mmsi = meta.get('MMSI')

        # messages are arriving
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Packet received: MMSI {mmsi}")

        if not mmsi or lat is None: return

        for port_name, box in PORTS.items():
            if (box[0][0] <= lat <= box[1][0]) and (box[0][1] <= lon <= box[1][1]):
                print(f" >>> Match Found: Ship in {port_name}!")
                
                # save raw history
                history_path = os.path.join(OUT_DIR, f"{port_name}_history.jsonl")
                with open(history_path, "a") as f:
                    f.write(message + "\n")

                # update and save latest file
                ship_registry[port_name][mmsi] = data
                summary_path = os.path.join(OUT_DIR, f"{port_name}_latest.json")
                with open(summary_path, "w") as f:
                    json.dump(list(ship_registry[port_name].values()), f, indent=4)
                break
    except Exception as e:
        print(f"Update error: {e}")

def on_open(ws):
    ws.send(json.dumps({
        "APIKey": API_KEY,
        "BoundingBoxes": [[[-90, -180], [90, 180]]],
        "FilterMessageTypes": ["PositionReport", "ShipStaticData"]
    }))

def run():
    if not os.path.exists(OUT_DIR): os.makedirs(OUT_DIR)
    while True:
        try:
            ws = websocket.WebSocketApp("wss://stream.aisstream.io/v0/stream",
                                      on_open=on_open, on_message=on_message)
            ws.run_forever()
        except: time.sleep(10)

if __name__ == "__main__":
    run()
