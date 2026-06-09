import requests

def test_intel_feed():
    print("[-] Connecting to the Threat Intel Grid...")
    
    # Using a free, public test API that returns JSON data
    url = "https://jsonplaceholder.typicode.com/todos/1"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        print("[+] Connection successful! Data received from grid:")
        print(f"    Payload ID: {data.get('id')}")
        print(f"    Status: Grid Online (Title: '{data.get('title')}')\n")
        
        # This mocks what happens when a real DOT event is found
        mock_hazards = [
            {
                "id": "DOT-9482",
                "lat": 33.884, 
                "lon": -84.512,
                "severity": "MAJOR",
                "description": "Standstill traffic on Interstate 75 North due to an obstruction."
            }
        ]
        return mock_hazards

    except requests.exceptions.RequestException as e:
        print(f"[X] Comms failure: Could not reach the grid. {e}")
        return []

if __name__ == "__main__":
    hazards = test_intel_feed()
    for h in hazards:
        print(f"[!] INTERNAL INTEL: {h['severity']} hazard flagged at ({h['lat']}, {h['lon']})")