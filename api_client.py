import os
import requests
from dotenv import load_dotenv

load_dotenv()

class BEMApiClient:
    def __init__(self, base_url=None, api_key=None):
        self.base_url = base_url or os.getenv("API_BASE_URL", "https://desafio.beminteligencia.com.br/api/v1")
        # Removing any trailing slash if present
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]
        
        self.api_key = api_key or os.getenv("API_KEY")
        self.headers = {
            "X-API-Key": self.api_key
        }

    def check_health(self):
        """
        GET /health
        Check API status. Note: /health is relative to root domain, not api/v1.
        """
        # Get root domain
        parts = self.base_url.split("/api/")
        root_url = parts[0]
        url = f"{root_url}/health"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": str(e)}

    def get_groups(self):
        """
        GET /api/v1/groups
        List groups and sensors in each group.
        """
        url = f"{self.base_url}/groups"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching groups: {e}")
            return None

    def get_sensors(self, sensor_type=None, group=None):
        """
        GET /api/v1/sensors
        List sensors, optionally filtered by type or group.
        """
        url = f"{self.base_url}/sensors"
        params = {}
        if sensor_type:
            params["type"] = sensor_type
        if group:
            params["group"] = group
            
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching sensors: {e}")
            return None

    def get_sensor_data(self, sensor_id, start="-30m", stop="now", limit=1000):
        """
        GET /api/v1/data
        Fetch readings for a specific sensor.
        Requires valid X-API-Key.
        """
        url = f"{self.base_url}/data"
        params = {
            "sensor": sensor_id,
            "start": start,
            "stop": stop,
            "limit": limit
        }
        
        if not self.api_key:
            raise ValueError("API Key is required to query sensor data. Check your .env file.")
            
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            
            # Specific error handling based on API specs
            if response.status_code == 401:
                raise ValueError("Unauthorized (401): Invalid or missing X-API-Key.")
            elif response.status_code == 404:
                raise ValueError(f"Not Found (404): Sensor '{sensor_id}' not found.")
            elif response.status_code == 429:
                raise RuntimeWarning("Rate Limit Exceeded (429): Too many requests. Retry with backoff.")
                
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"HTTP Request failed: {e}")
            return None

# Simple testing block when executing this file directly
if __name__ == "__main__":
    print("Testing BEMApiClient...")
    client = BEMApiClient()
    
    # 1. Health check
    health = client.check_health()
    print("API Health Check:", health)
    
    # 2. Test groups endpoint (public)
    print("\nFetching public groups...")
    groups = client.get_groups()
    if groups:
        print(f"Groups type: {type(groups)}")
        if isinstance(groups, dict):
            print("Keys in groups response:", list(groups.keys()))
            groups_list = groups.get("groups", list(groups.values())[0] if groups else [])
        else:
            groups_list = groups
            
        print(f"Successfully fetched {len(groups_list)} groups.")
        if groups_list:
            print("First group structure sample:", groups_list[0])
        for g in groups_list[:2]:
            if isinstance(g, dict):
                print(f" - Group ID: {g.get('id')} / Name: {g.get('label')}")
            else:
                print(f" - Group item: {g}")
            
    # 3. Test data retrieval (requires API key)
    test_sensor = "estoque_compressor_1"
    print(f"\nFetching data for sensor '{test_sensor}' (using start=-24h, limit=3)...")
    try:
        data = client.get_sensor_data(test_sensor, start="-24h", limit=3)
        if data:
            print("Successfully retrieved data!")
            print("Fields returned:", data.get("fields"))
            print("Points count:", len(data.get("points", [])))
            if data.get("points"):
                print("First point sample:", data["points"][0])
        else:
            print("No data returned or query failed.")
    except Exception as ex:
        print(f"Error querying data: {ex}")
