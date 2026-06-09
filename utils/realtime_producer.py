import redis
import json
import time
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from utils.wireshark_to_cesnet import convert_wireshark_to_cesnet

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

CAPTURE_FILE = 'data/realtime_capture.csv'

def send_to_redis():
    try:
        df = convert_wireshark_to_cesnet(CAPTURE_FILE, window_minutes=1)
        if df.empty:
            print("Aucun flow détecté")
            return 0
        for _, row in df.iterrows():
            data = row.to_dict()
            data['timestamp'] = time.time()
            r.lpush('network_flows', json.dumps(data))
            r.ltrim('network_flows', 0, 999)
        print(f"✅ {len(df)} flows envoyés dans Redis")
        return len(df)
    except Exception as e:
        print(f"Erreur : {e}")
        return 0

print("🚀 Producteur démarré — surveillance en continu...")
print("Ctrl+C pour arrêter\n")

while True:
    send_to_redis()
    time.sleep(5)