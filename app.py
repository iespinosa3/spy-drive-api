from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import math
import requests
from typing import Optional
from security_gateway import SecurityGateway

# THIS IS THE LINE THAT WAS MISSING!
app = FastAPI(title="Spy Drive Tactical API", version="2.0.0")

# --- GLOBAL INTELLIGENCE CONFIG ---
TOMTOM_API_KEY = "USByChd1hxLlX6SGEYQWLjRe0xb2JI5X"
TRIGGER_RADIUS_METERS = 30 
RADAR_RADIUS_METERS = 8000 # ~5 miles

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

def get_bounding_box(lat, lon, radius_meters):
    # 1 degree of latitude is roughly 111,000 meters
    lat_offset = radius_meters / 111000.0
    lon_offset = radius_meters / (111000.0 * math.cos(math.radians(lat)))
    
    min_lon = lon - lon_offset
    min_lat = lat - lat_offset
    max_lon = lon + lon_offset
    max_lat = lat + lat_offset
    
    return f"{min_lon},{min_lat},{max_lon},{max_lat}"

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

    # ==========================================
    # --- SIMULATION OVERRIDE (FOR LOCAL TESTING) ---
    # ==========================================
    # Change to False when you want live TomTom data
    RUNNING_SIMULATION = True 

    if RUNNING_SIMULATION:
        fake_road_path = [
            {"latitude": lat + 0.0010, "longitude": lon + 0.0010},
            {"latitude": lat + 0.0005, "longitude": lon + 0.0005},
            {"latitude": lat, "longitude": lon}
        ]
        
        return {
            "action": "PLAY_AUDIO",
            "event_type": "HAZARD",
            "display_alert": "SIMULATED HAZARD DETECTED",
            "narrative_script": "Tactical alert. Simulated test hazard detected on your route. Initiating memory bank test.",
            "hazard_path": fake_road_path
        }

    # ==========================================
    # 1. LIVE SURVEILLANCE INTERCEPT (TOMTOM API)
    # ==========================================
    if TOMTOM_API_KEY:
        bbox = get_bounding_box(lat, lon, RADAR_RADIUS_METERS)
        
        fields = "{incidents{properties{iconCategory,magnitudeOfDelay,events{description}},geometry{type,coordinates}}}"
        tomtom_url = f"https://api.tomtom.com/traffic/services/5/incidentDetails?key={TOMTOM_API_KEY}&bbox={bbox}&fields={fields}&language=en-US"
        
        try:
            response = requests.get(tomtom_url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                
                if "incidents" in data and len(data["incidents"]) > 0:
                    incident = data["incidents"][0]
                    properties = incident.get("properties", {})
                    delay_category = properties.get("magnitudeOfDelay", 0)
                    
                    if delay_category >= 2:
                        description = "Unknown obstruction"
                        if "events" in properties and len(properties["events"]) > 0:
                            description = properties["events"][0].get("description", "Unknown obstruction")
                        
                        formatted_path = []
                        if "geometry" in incident and "coordinates" in incident["geometry"]:
                            for point in incident["geometry"]["coordinates"]:
                                if len(point) == 2:
                                    formatted_path.append({
                                        "latitude": point[1],
                                        "longitude": point[0]
                                    })

                        return {
                            "action": "PLAY_AUDIO",
                            "event_type": "HAZARD",
                            "display_alert": "LIVE HAZARD DETECTED",
                            "narrative_script": f"Tactical alert. Live data intercept indicates {description} ahead. Reroute advised.",
                            "hazard_path": formatted_path 
                        }
        except Exception as e:
            print(f"Surveillance Intercept Failed: {e}")
            pass 

    # ==========================================
    # 2. TARGET DROP ZONE LOGIC
    # ==========================================
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
            "event_type": "TARGET_REACHED",
            "display_alert": "DROP ZONE REACHED",
            "narrative_script": "Perimeter breached. Secure the area and await the payload."
        }
    else:
        return {
            "action": "KEEP_MOVING",
            "display_alert": f"TARGET: {int(distance)} METERS"
        }
