from fastapi import FastAPI, HTTPException
import math
import requests
import random
from typing import Optional
from pydantic import BaseModel, Field
from security_gateway import SecurityGateway

app = FastAPI(title="Spy Drive Tactical API", version="3.0.0")

# --- MISSION SPECIFIC STORYLINE EVENT POOLS ---
MISSION_STORIES = {
    "DEFAULT": [
        {"type": "HAZARD", "description": "Police unit reported ahead. Maintain low profile."},
        {"type": "HAZARD", "description": "Surveillance detected. Keep moving, do not linger."},
        {"type": "INTEL", "description": "Covert objective updated. Proceed with extreme caution."}
    ],
    "SUPPLY_RUN": [
        {"type": "HAZARD", "description": "Supply route compromised. Reroute if intercepted."},
        {"type": "INTEL", "description": "Cache secured. Log coordinates and proceed."},
        {"type": "SUPPLY_RUN", "description": "High-grade stimulant cache detected nearby."}
    ],
    "COURIER": [
        {"type": "HAZARD", "description": "Hostile tail detected. Shake them before drop off."},
        {"type": "INTEL", "description": "Package is clear. Maintain speed and vector."},
        {"type": "COURIER", "description": "Untraceable currency drop available in this sector."}
    ],
    "COVER": [
        {"type": "HAZARD", "description": "Routine patrol spotted. Act natural."},
        {"type": "INTEL", "description": "Daily cover holding steady. No alerts."},
        {"type": "INTEL", "description": "Local fuel reserves located along current vector."}
    ],
    "SAFEHOUSE": [
        {"type": "HAZARD", "description": "Perimeter compromised. Find an alternate route."},
        {"type": "INTEL", "description": "Safehouse lockdown lifted. Clear to approach."},
        {"type": "INTEL", "description": "Home-lock active. Proceed securely to final waypoint."}
    ]
}

class TelemetryPacket(BaseModel):
    agent_id: str
    latitude: float
    longitude: float
    target_lat: Optional[float] = None
    target_lon: Optional[float] = None
    mission_profile: Optional[str] = "DEFAULT"

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
    # Security Gateway Validation
    validation = SecurityGateway.validate_telemetry(packet.latitude, packet.longitude, packet.agent_id)
    if validation["status"] == "REJECTED":
        raise HTTPException(status_code=400, detail=validation["reason"])
    
    lat, lon = validation["data"]["lat"], validation["data"]["lon"]

    # If no target exists, fall back to default awaiting state
    if packet.target_lat is None or packet.target_lon is None:
        return {"action": "KEEP_MOVING", "display_alert": "AWAITING TARGET", "route": []}

    # Calculate distance to target
    dist = calculate_distance(lat, lon, packet.target_lat, packet.target_lon)
    
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
    route_path = get_road_route(lat, lon, packet.target_lat, packet.target_lon)

    # Context-Aware Storyline Engine (Randomized Event per Mission Type)
    event = None
    # 5% chance per ping to trigger a narrative event to avoid repetition
    if random.random() < 0.05: 
        pool = MISSION_STORIES.get(packet.mission_profile, MISSION_STORIES["DEFAULT"])
        event = random.choice(pool)

    return {
        "action": "PLAY_AUDIO" if event else "KEEP_MOVING",
        "display_alert": event["type"] if event else f"TARGET: {int(dist)}m",
        "narrative_script": event["description"] if event else "",
        "route": route_path
    }
