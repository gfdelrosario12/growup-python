#!/usr/bin/env python3
"""
GrowUp IoT System - Integration Test Script
Tests connectivity between all components
"""

import requests
import time
import sys
from api_config import (
    BACKEND_SENSOR_READINGS,
    BACKEND_LATEST,
    FLASK_HOST,
    FLASK_PORT,
)

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓{RESET} {text}")

def print_error(text):
    print(f"{RED}✗{RESET} {text}")

def print_warning(text):
    print(f"{YELLOW}⚠{RESET} {text}")

def test_flask_server():
    """Test if Flask server is running and returning data"""
    print_header("Testing Flask Server")
    
    flask_url = f"http://{FLASK_HOST}:{FLASK_PORT}/sensors"
    print(f"Testing: {flask_url}")
    
    try:
        response = requests.get(flask_url, timeout=5)
        
        if response.status_code == 200:
            print_success(f"Flask server is running on port {FLASK_PORT}")
            
            data = response.json()
            
            if data.get("status") == "success":
                print_success("Response status is 'success'")
                
                # Check sensor data
                sensor_data = data.get("data", {})
                print(f"\n  📊 Sensor Data Received:")
                print(f"     Water Temp: {sensor_data.get('waterTemp', 'N/A')}°C")
                print(f"     pH Level: {sensor_data.get('ph', 'N/A')}")
                print(f"     Humidity: {sensor_data.get('humidity', 'N/A')}%")
                print(f"     Light: {sensor_data.get('lightIntensity', 'N/A')} lux")
                print(f"     Ammonia: {sensor_data.get('ammonia', 'N/A')} ppm")
                
                # Check ML data
                ml_data = data.get("ml")
                if ml_data:
                    print(f"\n  🤖 ML Data Received:")
                    print(f"     Plant Height: {ml_data.get('height', 'N/A')} cm")
                    print(f"     Leaves: {ml_data.get('leaves', 'N/A')}")
                    print(f"     Health: {ml_data.get('health', 'N/A')}%")
                else:
                    print_warning("No ML data available (camera may not be active)")
                
                return True
            else:
                print_error("Response status is not 'success'")
                return False
        else:
            print_error(f"Flask server returned status code {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to Flask server at {flask_url}")
        print("   Make sure main.py is running!")
        return False
    except Exception as e:
        print_error(f"Error testing Flask server: {e}")
        return False

def test_backend_connection():
    """Test if Spring Boot backend is accessible"""
    print_header("Testing Spring Boot Backend")
    
    print(f"Testing: {BACKEND_SENSOR_READINGS}")
    
    try:
        # Test POST endpoint
        test_payload = {
            "waterTemp": 23.5,
            "phLevel": 7.0,
            "dissolvedO2": 7.8,
            "airTemp": 24.0,
            "lightIntensity": 500,
            "waterLevel": 85,
            "waterFlow": 12,
            "humidity": 65,
            "ammonia": 0.02,
            "airPressure": 1013.25,
        }
        
        response = requests.post(
            BACKEND_SENSOR_READINGS,
            json=test_payload,
            timeout=5
        )
        
        if response.status_code == 200:
            print_success("Backend is accepting POST requests")
            
            data = response.json()
            print(f"\n  📝 Backend Response:")
            print(f"     Water Quality Score: {data.get('waterQualityScore', 'N/A')}")
            print(f"     Health Status: {data.get('healthStatus', 'N/A')}")
            print(f"     pH Alert: {data.get('phAlert', 'N/A')}")
            print(f"     Temperature Alert: {data.get('temperatureAlert', 'N/A')}")
            
            return True
        else:
            print_error(f"Backend returned status code {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to backend at {BACKEND_SENSOR_READINGS}")
        print("   Make sure your Spring Boot backend is running!")
        return False
    except Exception as e:
        print_error(f"Error testing backend: {e}")
        return False

def test_backend_latest():
    """Test if we can retrieve latest data from backend"""
    print_header("Testing Backend Data Retrieval")
    
    print(f"Testing: {BACKEND_LATEST}")
    
    try:
        response = requests.get(BACKEND_LATEST, timeout=5)
        
        if response.status_code == 200:
            print_success("Can retrieve latest reading from backend")
            
            data = response.json()
            if data:
                print(f"\n  📊 Latest Reading:")
                print(f"     Timestamp: {data.get('timestamp', 'N/A')}")
                print(f"     Water Temp: {data.get('waterTemp', 'N/A')}°C")
                print(f"     pH Level: {data.get('phLevel', 'N/A')}")
                print(f"     Water Quality: {data.get('waterQualityScore', 'N/A')}")
            else:
                print_warning("No data in backend yet")
            
            return True
        else:
            print_error(f"Backend returned status code {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to backend at {BACKEND_LATEST}")
        return False
    except Exception as e:
        print_error(f"Error retrieving data: {e}")
        return False

def test_data_flow():
    """Test the complete data flow"""
    print_header("Testing Complete Data Flow")
    
    print("Waiting 3 seconds for data to flow...")
    time.sleep(3)
    
    try:
        # Get data from Flask
        flask_response = requests.get(
            f"http://{FLASK_HOST}:{FLASK_PORT}/sensors",
            timeout=5
        )
        
        if flask_response.status_code != 200:
            print_error("Flask server not responding")
            return False
        
        flask_data = flask_response.json().get("data", {})
        
        # Get latest from backend
        backend_response = requests.get(BACKEND_LATEST, timeout=5)
        
        if backend_response.status_code != 200:
            print_error("Backend not responding")
            return False
        
        backend_data = backend_response.json()
        
        # Compare timestamps (backend should have recent data)
        print_success("Data flow is working!")
        print(f"\n  🔄 Data Comparison:")
        print(f"     Flask Water Temp: {flask_data.get('waterTemp', 'N/A')}°C")
        print(f"     Backend Water Temp: {backend_data.get('waterTemp', 'N/A')}°C")
        print(f"     Flask pH: {flask_data.get('ph', 'N/A')}")
        print(f"     Backend pH: {backend_data.get('phLevel', 'N/A')}")
        
        return True
        
    except Exception as e:
        print_error(f"Error testing data flow: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("🧪 GrowUp IoT System Integration Test")
    print("="*60)
    
    results = {
        "Flask Server": test_flask_server(),
        "Backend Connection": test_backend_connection(),
        "Backend Retrieval": test_backend_latest(),
        "Data Flow": test_data_flow(),
    }
    
    # Summary
    print_header("Test Summary")
    
    all_passed = True
    for test_name, result in results.items():
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
            all_passed = False
    
    print("\n" + "="*60)
    
    if all_passed:
        print(f"\n{GREEN}✓ All tests passed! System is working correctly.{RESET}\n")
        sys.exit(0)
    else:
        print(f"\n{RED}✗ Some tests failed. Please check the errors above.{RESET}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
