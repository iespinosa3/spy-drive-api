from fastapi import FastAPI, HTTPException
import math
import requests
from typing import Optional
from pydantic import BaseModel, Field

app = FastAPI(title="Spy Drive Tactical API", version="3.0.0")

# --- CONFIG ---
PROXIMITY_RADIUS_METERS = 50
SUPPLY_DROPS = [
    {"id": "drop_1", "lat": 33.8843, "lon": -84.5161, "type": "Untraceable Currency", "description": "Untraceable currency drop available."},
    {"id": "drop_2", "lat": 33.8964, "lon": -84.5186, "type": "Stimulant Cache", "description": "High-grade stimulant cache detected."},
    {"id": "drop_3", "lat": 33.8741, "lon": -84.5020, "type": "Fuel Depot", "description": "Local fuel reserves located."}
]

class TelemetryPacket(BaseModel):
    agent_id: str
    latitude: float
    longitude: float
    target_lat: Optional[float] = None
    target_lon: Optional[float] = None
    mission_profile: Optional[str] = "DEFAULT"

def get_road_route(lat1, lon1, lat2, lon2):
    # Public OSRM demo: Using a fallback strategy
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('routes'):
                coords = data['routes'][0]['geometry']['coordinates']
                return [{"latitude": c[1], "longitude": c[0]} for c in coords]
    except Exception as e:
        print(f"OSRM Error: {e}")
    return [] # ALWAYS return empty list, NEVER None

@app.post("/api/v1/telemetry")
async def process_agent_movement(packet: TelemetryPacket):
    try:
        lat, lon = packet.latitude, packet.longitude
        
        # Calculate route: ALWAYS a list
        route_path = get_road_route(lat, lon, packet.target_lat, packet.target_lon) if packet.target_lat else []
        
        # Check Supply Drops
        for drop in SUPPLY_DROPS:
            # Using simple distance check
            if abs(lat - drop["lat"]) < 0.01 and abs(lon - drop["lon"]) < 0.01:
                return {
                    "action": "PLAY_AUDIO", "event_type": "SUPPLY_DROP",
                    "display_alert": f"ASSET: {drop['type'].upper()}",
                    "route": route_path
                }

        # Default movement response
        return {
            "action": "KEEP_MOVING",
            "display_alert": "TARGET LOCKED" if packet.target_lat else "AWAITING TARGET",
            "route": route_path
        }
    except Exception as e:
        # If anything crashes, return valid JSON error so the app doesn't break
        return {"action": "ERROR", "message": str(e), "route": []}
