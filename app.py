from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import math
from typing import Optional
from security_gateway import SecurityGateway

app = FastAPI(title="Spy Drive Tactical API", version="1.0.0")

TRIGGER_RADIUS_METERS = 30 

# Define the structure of incoming requests using Pydantic
class TelemetryPacket(BaseModel):
    agent_id: str = Field(..., example="Agent007")
    latitude: float = Field(..., example=33.891)
    longitude: float = Field(..., example=-84.519)
    # The new dynamic target variables
    target_lat: Optional[float] = None
    target_lon: Optional[float] = None

# Calculates distance between two GPS points in meters
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371e3 
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi/2.0)**2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda/2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

@app.post("/api/v1/telemetry")
async def process_agent_movement(packet: TelemetryPacket):
    validation = SecurityGateway.validate_telemetry(
        packet.latitude, 
        packet.longitude, 
        packet.agent_id
    )
    
    if validation["status"] == "REJECTED":
        raise HTTPException(status_code=400, detail=validation["reason"])
    
    clean_data = validation["data"]
    lat = clean_data["lat"]
    lon = clean_data["lon"]
    
    # If no target is set on the phone yet, just acknowledge the route
    if packet.target_lat is None or packet.target_lon is None:
        return {
            "action": "KEEP_MOVING",
            "display_alert": "AWAITING TARGET COORDINATES",
            "narrative_script": None
        }

    # If a target IS set, calculate the dynamic distance
    distance = calculate_distance(lat, lon, packet.target_lat, packet.target_lon)
    
    if distance <= TRIGGER_RADIUS_METERS:
        return {
            "action": "PLAY_AUDIO",
            "display_alert": "DROP ZONE REACHED",
            "narrative_script": "Perimeter breached. Secure the area and await the payload."
        }
    else:
        return {
            "action": "KEEP_MOVING",
            "display_alert": f"TARGET: {int(distance)} METERS"
        }
