import requests
import json

# Example POST request to test the server
url = "http://localhost:8000/forecast"

# Test data 
test_data = {
    "name": "New forecast",
    "urgency": "low",
    "type": "new_forecast",
    "model": "WeatherMesh",
    "initialization_time": "2025-05-18T00:00:00.000Z",
    "forecast_hours": [1, 2, 3, 6, 12, 24, 48, 72]  # Shortened for testing
}

test_data_intracycle = {
    "name": "Intracycle Test",
    "model": "WeatherMesh:intracycle",
    "initialization_time": "2025-05-18T00:00:00.000Z",
    "forecast_hours": [3]
}

test_data_ensemble = {
    "name": "Ensemble Mean Test",
    "model": "WeatherMesh:ens:mean",
    "initialization_time": "2025-05-18T00:00:00.000Z",
    "forecast_hours": [1, 2]
}

def run_forecast_test(test_name, data, post_url):
    print(f"\n--- Testing: {test_name} ---")
    try:
        response = requests.post(post_url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e} - Response text: {response.text}")

# Run tests
run_forecast_test("Default WeatherMesh Model", test_data, url)
run_forecast_test("WeatherMesh Intracycle Model", test_data_intracycle, url)
run_forecast_test("WeatherMesh Ensemble Mean Model", test_data_ensemble, url)

# Test health endpoint
print("\n--- Testing: Health Endpoint ---")
health_response = requests.get("http://localhost:8000/health")
print(f"\nHealth Check: {health_response.json()}")

# Test status endpoint
print("\n--- Testing: Status Endpoint ---")
status_response = requests.get("http://localhost:8000/status")
print(f"\nStatus: {status_response.json()}")
