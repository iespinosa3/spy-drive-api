from fastapi import FastAPI, HTTPException
import math
import requests
from typing import Optional
from pydantic import BaseModel, Field

app = FastAPI(title="Spy Drive Tactical API", version="3.0.0")

class TelemetryPacket(BaseModel):
    agent_id: str
    latitude: float
    longitude: float
    target_lat: Optional[float] = None
    target_lon: Optional[float] = None
    is_off_course: Optional[bool] = False

def get_road_route(lat1, lon1, lat2, lon2):
    # Using OSRM (No API Key Required)
    url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('routes'):
                coords = data['routes'][0]['geometry']['coordinates']
                return [{"latitude": c[1], "longitude": c[0]} for c in coords]
    except Exception:
        pass
    return []

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371e3  # Earth's radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi/2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2.0)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

@app.post("/api/v1/telemetry")
async def process_agent_movement(packet: TelemetryPacket):
    # Calculate distance if a target exists
    if packet.target_lat:
        dist = calculate_distance(packet.latitude, packet.longitude, packet.target_lat, packet.target_lon)
        
        # If within 100m, notify and clear target
        if dist <= 100:
            return {
                "action": "PLAY_AUDIO",
                "display_alert": "DESTINATION REACHED",
                "narrative_script": "Destination reached, Agent.",
                "route": [], # Clear route
                "clear_target": True # Signal to app to clear inputs
            }
        
        # Standard route calculation
        route_path = get_road_route(packet.latitude, packet.longitude, packet.target_lat, packet.target_lon)
        return {
            "action": "KEEP_MOVING",
            "display_alert": f"TARGET: {int(dist)}m",
            "narrative_script": "",
            "route": route_path
        }
    
    return {"action": "KEEP_MOVING", "display_alert": "AWAITING TARGET", "route": []}
