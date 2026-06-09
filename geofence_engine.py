import math

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points 
    on the Earth using the Haversine formula.
    Returns distance in miles.
    """
    # Earth's radius in miles
    R = 3958.8
    
    # Convert latitude and longitude from degrees to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = (math.sin(delta_phi / 2) ** 2 + 
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    
    return distance

def check_agent_perimeter(agent_lat, agent_lon, hazards, trigger_radius_miles=2.0):
    """
    Compares the agent's current location against a list of known hazards.
    Triggers an alert if a hazard is inside the perimeter.
    """
    for hazard in hazards:
        distance = calculate_distance(agent_lat, agent_lon, hazard['lat'], hazard['lon'])
        
        if distance <= trigger_radius_miles:
            print(f"\n[!!!] PERIMETER BREACHED [!!!]")
            print(f"Distance to objective: {distance:.2f} miles.")
            print(f"Narrative Trigger: 'Agent, {hazard['description']}'")
            return True
            
    print(f"Perimeter secure. Nearest hazard is outside the {trigger_radius_miles} mile radius.")
    return False

# --- Test Environment ---
if __name__ == "__main__":
    # Simulated database of live hazards from your threat_intel_service.py
    live_hazards = [
        {
            "id": "DOT-9482",
            "lat": 33.884, 
            "lon": -84.512,
            "spy_description": "Satellite imagery shows a massive vehicle pileup on I-75. Enemy operatives have effectively blocked the highway. Recalculating route to avoid capture."
        }
    ]
    
    # Simulated live GPS updates from the driver's phone
    print("Scenario A: Agent is far away.")
    check_agent_perimeter(agent_lat=33.950, agent_lon=-84.550, hazards=live_hazards)
    
    print("\nScenario B: Agent approaches the hot zone.")
    check_agent_perimeter(agent_lat=33.890, agent_lon=-84.515, hazards=live_hazards)