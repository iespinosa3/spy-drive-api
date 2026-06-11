from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import math
from typing import Optional
from security_gateway import SecurityGateway

app = FastAPI(title="Spy Drive Tactical API", version="1.1.0")

# --- THE HAZARD DATABASE ---
# (You can change these coordinates to a spot near you to test!)
active_hazards = [
    {
        "id": "DOT-9482",
        "lat": 33.9023, 
        "lon": -84.5387,
        "description": "Standstill traffic on Interstate 75 North due to an obstruction."
    }
]

TRIGGER_RADIUS_METERS = 30 
HAZARD_WARNING_METERS = 800 # Warn the agent if they get within 800 meters (half a mile) of a hazard

class TelemetryPacket(BaseModel):
    agent_id: str = Field(..., example="Agent007")
    latitude: float = Field(..., example=33.891)
    longitude: float = Field(..., example=-84.519)
    target_lat: Optional[float] = None
    target_lon: Optional[float] = None

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371e3 
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi/2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

@app.post("/api/v1/telemetry")
async def process_agent_movement(packet: TelemetryPacket):
    validation = SecurityGateway.validate_telemetry(
        packet.latitude, packet.longitude, packet.agent_id
    )
    if validation["status"] == "REJECTED":
        raise HTTPException(status_code=400, detail=validation["reason"])
    
    clean_data = validation["data"]
    lat = clean_data["lat"]
    lon = clean_data["lon"]
    
    # 1. SCAN FOR HAZARDS (Priority Override)
    for hazard in active_hazards:
        hazard_dist = calculate_distance(lat, lon, hazard["lat"], hazard["lon"])
        if hazard_dist <= HAZARD_WARNING_METERS:
            return {
                "action": "PLAY_AUDIO",
                "event_type": "HAZARD", # Tells the phone NOT to delete the target
                "display_alert": "HAZARD DETECTED",
                "narrative_script": f"Warning. Hazard detected ahead. {hazard['description']} Reroute advised."
            }

    # 2. SCAN FOR TARGET DROP ZONE
    if packet.target_lat is None or packet.target_lon is None:
        return {
            "action": "KEEP_MOVING",
            "display_alert": "AWAITING TARGET COORDINATES",
            "narrative_script": None
        }

    distance = calculate_distance(lat, lon, packet.target_lat, packet.target_lon)
    
    if distance <= TRIGGER_RADIUS_METERS:
        return {
            "action": "PLAY_AUDIO",
            "event_type": "TARGET_REACHED", # Tells the phone to clear the target
            "display_alert": "DROP ZONE REACHED",
            "narrative_script": "Perimeter breached. Secure the area and await the payload."
        }
    else:
        return {
            "action": "KEEP_MOVING",
            "display_alert": f"TARGET: {int(distance)} METERS"
        }
