from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import math

from security_gateway import SecurityGateway
# Temporarily commenting out the advanced engines for the Field Test
# from geofence_engine import check_agent_perimeter
# from supply_drop_engine import SupplyDropEngine
# from hq_comms import generate_mission_script

app = FastAPI(title="Spy Drive Tactical API", version="1.0.0")

# --- THE TARGET DROP ZONE (FIELD TEST) ---
# Replace these with coordinates slightly down the street from your current location!
TARGET_LAT = 34.902029 
TARGET_LNG = -74.538694 
TRIGGER_RADIUS_METERS = 30 # How close you need to get to trigger the audio

# Define the structure of incoming requests using Pydantic
class TelemetryPacket(BaseModel):
    agent_id: str = Field(..., example="Agent007")
    latitude: float = Field(..., example=33.891)
    longitude: float = Field(..., example=-84.519)

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
    # 1. Route through the Security Gateway
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
    
    # 2. ISOLATED TARGET DISTANCE TEST
    distance = calculate_distance(lat, lon, TARGET_LAT, TARGET_LNG)
    
    # 3. Trigger the Breach Audio or Update the Countdown HUD
    if distance <= TRIGGER_RADIUS_METERS:
        return {
            "action": "PLAY_AUDIO",
            "display_alert": "DROP ZONE REACHED",
            "narrative_script": "Perimeter breached. You have arrived at the target coordinates. Secure the area and await the payload."
        }
    else:
        return {
            "action": "KEEP_MOVING",
            "display_alert": f"TARGET: {int(distance)} METERS"
        }
