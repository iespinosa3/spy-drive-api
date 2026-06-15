from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import math
import requests
from typing import Optional
from security_gateway import SecurityGateway

app = FastAPI(title="Spy Drive Tactical API", version="2.0.0")

# --- GLOBAL INTELLIGENCE CONFIG ---
TOMTOM_API_KEY = "USByChd1hxLlX6SGEYQWLjRe0xb2JI5X"
TRIGGER_RADIUS_METERS = 30 
RADAR_RADIUS_METERS = 8000 # ~5 miles

PROXIMITY_RADIUS_METERS = 50 # Trigger distance for a supply drop (approx 160 feet)

# --- THE LOCAL GEOFENCE (SMYRNA SECTOR) ---
SUPPLY_DROPS = [
    {
        "id": "drop_1", 
        "lat": 33.8843, "lon": -84.5161, # Smyrna Market Village
        "type": "Untraceable Currency", 
        "description": "Untraceable currency drop available."
    },
    {
        "id": "drop_2", 
        "lat": 33.8964, "lon": -84.5186, # Rev Coffee
        "type": "Stimulant Cache", 
        "description": "High-grade stimulant cache detected."
    },
    {
        "id": "drop_3", 
        "lat": 33.8741, "lon": -84.5020, # QuikTrip Atlanta Rd
        "type": "Fuel Depot", 
        "description": "Local fuel reserves located."
    }
]

class TelemetryPacket(BaseModel):
    agent_id: str = Field(..., example="Agent007")
    latitude: float = Field(..., example=33.891)
    longitude: float = Field(..., example=-84.519)
    target_lat: Optional[float] = None
    target_lon: Optional[float] = None
    mission_profile: Optional[str] = "DEFAULT" # Receives the mission type

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
    profile = packet.mission_profile

    # --- THE NARRATIVE STORYBOARD DICTIONARY ---
    MISSION_SCRIPTS = {
        "DEFAULT": {
            "hazard": "Tactical alert, {agent}. Live data intercept indicates {obstruction} ahead. Reroute advised.",
            "arrival": "{agent}, perimeter breached. Secure the area and await the payload."
        },
        "SUPPLY_RUN": {
            "hazard": "Supply route compromised, {agent}. Intercept indicates {obstruction}. Adjusting approach vector to preserve rations.",
            "arrival": "Supply depot reached, {agent}. Secure the perimeter, acquire rations, and exfiltrate cleanly."
        },
        "COURIER": {
            "hazard": "Courier route obstructed by {obstruction}. Time is a factor, {agent}. Rerouting to ensure asset delivery.",
            "arrival": "Dead drop reached, {agent}. Transfer the asset and clear the zone immediately."
        },
        "COVER": {
            "hazard": "Civilian traffic anomaly detected: {obstruction}. Maintain cover profile while navigating the delay, {agent}.",
            "arrival": "Primary cover location reached. Blend in, {agent}. Uplink suspended until shift concludes."
        },
        "SAFEHOUSE": {
            "hazard": "Approach vector compromised. {obstruction} detected. Do not draw attention on your final approach, {agent}.",
            "arrival": "Safehouse reached. Secure the vehicle, {agent}, sweep the perimeter, and lay low."
        }
    }

    current_scripts = MISSION_SCRIPTS.get(profile, MISSION_SCRIPTS["DEFAULT"])
    
    # ==========================================
    # 1. LIVE SURVEILLANCE INTERCEPT (TOMTOM API)
    # ==========================================
    if TOMTOM_API_KEY: # FIXED: Only checks if key exists
        bbox = get_bounding_box(lat, lon, RADAR_RADIUS_METERS)
        
        # FIXED: Added geometry request back to fields
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
                        
                        # FIXED: Restored the code to extract road geometry
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
                            "narrative_script": current_scripts["hazard"].format(
                                agent=packet.agent_id, 
                                obstruction=description
                            ),
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
            "narrative_script": None # FIXED: Removed accidental script format
        }

    distance = calculate_distance(lat, lon, packet.target_lat, packet.target_lon)
    
    if distance <= TRIGGER_RADIUS_METERS:
        return {
            "action": "PLAY_AUDIO",
            "event_type": "TARGET_REACHED",
            "display_alert": "DROP ZONE REACHED",
            "narrative_script": current_scripts["arrival"].format(
                agent=packet.agent_id
            )
        }
    else:# ==========================================
    # 3. PROXIMITY RADAR (SUPPLY DROPS)
    # ==========================================
     for drop in SUPPLY_DROPS:
        drop_dist = calculate_distance(lat, lon, drop["lat"], drop["lon"])
        if drop_dist <= PROXIMITY_RADIUS_METERS:
            return {
                "action": "PLAY_AUDIO",
                "event_type": "SUPPLY_DROP",
                "display_alert": f"ASSET DETECTED: {drop['type'].upper()}",
                "narrative_script": f"Tactical radar ping. {packet.agent_id}, {drop['description']} Proceed if rations are required."
                # NEW: Send the coordinates to the phone so it can reroute!
                "drop_lat": drop["lat"],
                "drop_lon": drop["lon"]
            }

    # If no hazards, no targets, and no supply drops:
    return {
        "action": "KEEP_MOVING",
        "display_alert": f"TARGET: {int(distance)} METERS" if packet.target_lat else "AWAITING TARGET COORDINATES"
    }
  
