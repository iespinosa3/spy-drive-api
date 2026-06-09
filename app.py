from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from security_gateway import SecurityGateway
from geofence_engine import check_agent_perimeter
from supply_drop_engine import SupplyDropEngine
from hq_comms import generate_mission_script

app = FastAPI(title="Spy Drive Tactical API", version="1.0.0")
ad_engine = SupplyDropEngine()

# Hardcoded mock hazards for the web instance
active_hazards = [
    {
        "id": "DOT-9482",
        "lat": 33.884, 
        "lon": -84.512,
        "description": "Standstill traffic on Interstate 75 North due to an obstruction."
    }
]

# Define the structure of incoming requests using Pydantic
class TelemetryPacket(BaseModel):
    agent_id: str = Field(..., example="Agent007")
    latitude: float = Field(..., example=33.891)
    longitude: float = Field(..., example=-84.519)

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
    
    # 2. Check for Traffic Hazards
    hazard_tripped = check_agent_perimeter(lat, lon, active_hazards, trigger_radius_miles=1.5)
    
    if hazard_tripped:
        narrative = generate_mission_script("HAZARD", "Interstate 75 North", active_hazards[0]['description'])
        return {
            "action": "PLAY_AUDIO",
            "display_alert": "HAZARD AHEAD",
            "narrative_script": narrative
        }
        
    # 3. Check for Supply Drops
    nearby_drops = ad_engine.get_nearby_supply_drops(lat, lon, search_radius_miles=1.0)
    if nearby_drops:
        drop = nearby_drops[0]
        narrative = generate_mission_script("SUPPLY_DROP", drop['name'], drop['deal'])
        return {
            "action": "PLAY_AUDIO",
            "display_alert": "SUPPLY DROP INBOUND",
            "narrative_script": narrative
        }
        
    return {
        "action": "KEEP_MOVING",
        "display_alert": "ROUTE CLEAR",
        "narrative_script": None
    }