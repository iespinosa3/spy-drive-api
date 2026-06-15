from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import math
import requests
from typing import Optional
from security_gateway import SecurityGateway

app = FastAPI(title="Spy Drive Tactical API", version="2.0.0")

# --- CONFIG ---
TOMTOM_API_KEY = "USByChd1hxLlX6SGEYQWLjRe0xb2JI5X"
TRIGGER_RADIUS_METERS = 30
RADAR_RADIUS_METERS = 8000
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

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371e3
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi/2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2.0)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

def get_road_route(lat1, lon1, lat2, lon2):
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
    return [] # Return empty list, never None

@app.post("/api/v1/telemetry")
async def process_agent_movement(packet: TelemetryPacket):
    validation = SecurityGateway.validate_telemetry(packet.latitude, packet.longitude, packet.agent_id)
    if validation["status"] == "REJECTED":
        raise HTTPException(status_code=400, detail=validation["reason"])
    
    lat, lon = validation["data"]["lat"], validation["data"]["lon"]
    
    # Calculate route if target exists, default to empty list
    route_path = get_road_route(lat, lon, packet.target_lat, packet.target_lon) if packet.target_lat else []

    # Check Supply Drops
    for drop in SUPPLY_DROPS:
        if calculate_distance(lat, lon, drop["lat"], drop["lon"]) <= PROXIMITY_RADIUS_METERS:
            return {
                "action": "PLAY_AUDIO", "event_type": "SUPPLY_DROP",
                "display_alert": f"ASSET: {drop['type'].upper()}",
                "narrative_script": f"Tactical radar ping. {packet.agent_id}, {drop['description']}",
                "drop_lat": drop["lat"], "drop_lon": drop["lon"], "route": route_path
            }

    # Check Target Arrival
    if packet.target_lat and calculate_distance(lat, lon, packet.target_lat, packet.target_lon) <= TRIGGER_RADIUS_METERS:
        return {"action": "PLAY_AUDIO", "event_type": "TARGET_REACHED", "display_alert": "DROP ZONE REACHED", "route": route_path}

    # Default
    dist = int(calculate_distance(lat, lon, packet.target_lat, packet.target_lon)) if packet.target_lat else 0
    return {
        "action": "KEEP_MOVING",
        "display_alert": f"TARGET: {dist} METERS" if packet.target_lat else "AWAITING TARGET",
        "route": route_path
    }
