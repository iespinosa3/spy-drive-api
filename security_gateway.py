import re

class SecurityGateway:
    @staticmethod
    def sanitize_coordinate(value):
        """
        Ensures coordinates are strictly numbers or floats, 
        stripping out characters used in injection attacks.
        """
        if isinstance(value, (int, float)):
            return float(value)
            
        # If it's a string, strip malicious symbols and check if it's a valid decimal
        if isinstance(value, str):
            clean_str = re.sub(r'[^\d\.\-]', '', value)
            try:
                return float(clean_str)
            except ValueError:
                return None
        return None

    @staticmethod
    def validate_telemetry(raw_lat, raw_lon, agent_id):
        """
        Validates incoming agent data against known physical boundaries 
        and injection attack patterns.
        """
        # 1. Sanitize Agent ID (A03: Injection prevention)
        # Ensure it contains only standard alphanumeric characters (no SQL characters)
        clean_agent_id = re.sub(r'[^a-zA-Z0-9\-_]', '', str(agent_id))
        if not clean_agent_id or clean_agent_id != str(agent_id):
            return {"status": "REJECTED", "reason": "Malicious or malformed Agent ID detected."}

        # 2. Parse and sanitize coordinates
        lat = SecurityGateway.sanitize_coordinate(raw_lat)
        lon = SecurityGateway.sanitize_coordinate(raw_lon)

        if lat is None or lon is None:
            return {"status": "REJECTED", "reason": "Non-numeric coordinate injection attempt."}

        # 3. Boundary Validation (Physical sanity limits)
        # Latitude must be between -90 and 90. Longitude must be between -180 and 180.
        if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
            return {"status": "REJECTED", "reason": "Coordinates out of bounds (Impossibility defense)."}

        # 4. Payload Approved
        return {
            "status": "APPROVED",
            "data": {
                "agent_id": clean_agent_id,
                "lat": lat,
                "lon": lon
            }
        }

# --- Sandbox Security Test ---
if __name__ == "__main__":
    gateway = SecurityGateway()

    # Test Case 1: Legitimate Agent Telemetry
    print("Testing Normal Stream:")
    print(gateway.validate_telemetry(33.884, -84.512, "Agent007"))

    # Test Case 2: SQL Injection Attempt in Coordinates
    print("\nTesting SQL Injection Attempt:")
    print(gateway.validate_telemetry("33.884; DROP TABLE Users;--", -84.512, "Agent007"))

    # Test Case 3: Out-of-Bounds Location Spoofing
    print("\nTesting Impossible Coordinates:")
    print(gateway.validate_telemetry(125.0, -84.512, "Agent007"))