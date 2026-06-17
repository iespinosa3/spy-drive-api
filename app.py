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
    mission_profile: Optional[str] = "DEFAULT"

def get_road_route(lat1, lon1, lat2, lon2):
    # Standard OSRM production endpoint
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

@app.post("/api/v1/telemetry")
async def process_agent_movement(packet: TelemetryPacket):
    # Harsh narrative logic based on route deviation
    narrative = f"Maintain vector, {packet.agent_id}."
    if packet.is_off_course:
        narrative = "You are failing the mission, Agent. Return to the path immediately."

    # Generate route if target exists
    route_path = get_road_route(packet.latitude, packet.longitude, packet.target_lat, packet.target_lon) if packet.target_lat else []

    return {
        "action": "KEEP_MOVING",
        "display_alert": "TARGET LOCKED" if packet.target_lat else "AWAITING TARGET",
        "narrative_script": narrative,
        "route": route_path
    }
