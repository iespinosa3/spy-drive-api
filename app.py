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
    # 1. LIVE SURVEILLANCE INTERCEPT (TOMTOM API)
    # ==========================================
    if TOMTOM_API_KEY != "USByChd1hxLlX6SGEYQWLjRe0xb2JI5X":
        bbox = get_bounding_box(lat, lon, RADAR_RADIUS_METERS)
        
        # UPDATED: We added 'geometry{type,coordinates}' to the fields request!
        fields = "{incidents{properties{iconCategory,magnitudeOfDelay,events{description}},geometry{type,coordinates}}}"
        tomtom_url = f"https://api.tomtom.com/traffic/services/5/incidentDetails?key={TOMTOM_API_KEY}&bbox={bbox}&fields={fields}&language=en-US"
        
        try:
            response = requests.get(tomtom_url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                
                if "incidents" in data and len(data["incidents"]) > 0:
                    # Grab the closest incident
                    incident = data["incidents"][0]
                    properties = incident.get("properties", {})
                    delay_category = properties.get("magnitudeOfDelay", 0)
                    
                    if delay_category >= 2:
                        description = "Unknown obstruction"
                        if "events" in properties and len(properties["events"]) > 0:
                            description = properties["events"][0].get("description", "Unknown obstruction")
                        
                        # NEW: Extract the road geometry
                        formatted_path = []
                        if "geometry" in incident and "coordinates" in incident["geometry"]:
                            # TomTom gives us [longitude, latitude]. 
                            # React Native needs {latitude: Y, longitude: X}. We translate it here.
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
                            "hazard_path": formatted_path # We send the road shape down to the phone!
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
