import time
from geofence_engine import calculate_distance  # Reusing our Haversine math

class SupplyDropEngine:
    def __init__(self):
        # Simulated database of ad campaigns
        self.campaign_database = [
            {
                "store_id": "LOC-CHEVRON-01",
                "name": "Chevron Station",
                "lat": 33.892,
                "lon": -84.518,
                "deal": "Free energy drink with fill-up",
                "spy_flavor": "HQ has authorized a chemical stamina boost. Pull into the Chevron depot ahead for a complimentary liquid fuel cells upgrade.",
                "cooldown_seconds": 300  # 5 minutes minimum before showing this ad again
            },
            {
                "store_id": "LOC-BURGER-02",
                "name": "Burger Shack",
                "lat": 33.875,
                "lon": -84.505,
                "deal": "20% off meals",
                "spy_flavor": "Agent, your biometric readings show low caloric reserves. A safehouse disguised as Burger Shack is offering a 20% discount on rations ahead.",
                "cooldown_seconds": 600
            }
        ]
        # Tracking history to prevent ad spamming
        self.ad_cooldown_tracker = {}

    def get_nearby_supply_drops(self, agent_lat, agent_lon, search_radius_miles=1.5):
        """
        Scans the database for valid, non-cooldown ads within range.
        """
        current_time = time.time()
        active_drops = []

        for store in self.campaign_database:
            store_id = store["store_id"]

            # 1. Check Frequency Capping (Cooldown)
            if store_id in self.ad_cooldown_tracker:
                last_triggered = self.ad_cooldown_tracker[store_id]
                if current_time - last_triggered < store["cooldown_seconds"]:
                    continue  # Skip this ad, it triggered too recently

            # 2. Calculate Exact Distance
            distance = calculate_distance(agent_lat, agent_lon, store["lat"], store["lon"])

            # 3. Trigger if inside the geofence
            if distance <= search_radius_miles:
                active_drops.append(store)
                # Log the trigger time to lock the cooldown
                self.ad_cooldown_tracker[store_id] = current_time

        return active_drops

# --- Test Environment ---
if __name__ == "__main__":
    engine = SupplyDropEngine()
    
    # Driver is cruising down the road
    current_driver_lat = 33.891
    current_driver_lon = -84.519
    
    print("[-] Scanning for authorized supply drops...")
    drops = engine.get_nearby_supply_drops(current_driver_lat, current_driver_lon)
    
    if drops:
        for drop in drops:
            print(f"\n[SUPPLY DROP DETECTED]: {drop['name']}")
            print(f"Merchant Deal: {drop['deal']}")
            print(f"HQ Comms Audio: '{drop['spy_flavor']}'")
    else:
        print("No drop zones in this sector.")

    # Simulating hitting the exact same spot 10 seconds later
    print("\n[-] Driver passes the same store 10 seconds later (Testing Cooldown)...")
    drops_again = engine.get_nearby_supply_drops(current_driver_lat, current_driver_lon)
    if not drops_again:
        print("[System] Ad suppressed by frequency capping engine. Driver is not spammed.")