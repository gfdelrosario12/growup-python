"""
Backend API Client Module
=========================
Provides a reusable interface for sending data to Spring Boot backend endpoints.
"""

import requests
import json
import time
from typing import Dict, Optional, Any

class BackendClient:
    """
    Unified client for communicating with Spring Boot backend.
    Handles sensor readings, plant growth, and ML results.
    """
    
    def __init__(self, base_url: str = "http://localhost:8080", timeout: int = 10, verbose: bool = False):
        """
        Initialize backend client.
        
        Args:
            base_url: Base URL of backend (e.g., http://localhost:8080)
            timeout: Request timeout in seconds
            verbose: Enable verbose logging
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.verbose = verbose
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def _log(self, message: str):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(message)
    
    def _post(self, endpoint: str, payload: Dict) -> bool:
        """
        Generic POST method for backend endpoints.
        
        Args:
            endpoint: Endpoint path (e.g., /api/sensor-readings)
            payload: JSON payload to POST
        
        Returns:
            bool: True if successful (200 OK), False otherwise
        """
        if not payload:
            return False
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.post(
                url,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self._log(f"✅ POST {endpoint} | Status: 200 OK")
                return True
            else:
                print(f"⚠️  {endpoint} returned {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"⚠️  Request timeout ({self.timeout}s) to {url}")
            return False
        except requests.exceptions.ConnectionError:
            print(f"⚠️  Cannot connect to {url}")
            return False
        except Exception as e:
            print(f"❌ Error posting to {endpoint}: {e}")
            return False
    
    def send_sensor_reading(self, 
                           waterTemp: float,
                           phLevel: float,
                           waterLevel: float,
                           waterFlow: float,
                           lightIntensity: float,
                           humidity: float,
                           airTemp: float,
                           airPressure: float) -> bool:
        """
        Send sensor reading to /api/sensor-readings.
        
        Args:
            All 8 sensor values as floats
        
        Returns:
            bool: True if successful
        """
        payload = {
            "waterTemp": waterTemp,
            "phLevel": phLevel,
            "waterLevel": waterLevel,
            "waterFlow": waterFlow,
            "lightIntensity": lightIntensity,
            "humidity": humidity,
            "airTemp": airTemp,
            "airPressure": airPressure
        }
        return self._post("/api/sensor-readings", payload)
    
    def send_plant_growth(self,
                         deviceId: str,
                         plantName: str,
                         species: str,
                         growthStage: str,
                         healthStatus: str,
                         cameraDetections: Optional[Dict] = None,
                         timestamp: Optional[str] = None) -> bool:
        """
        Send plant growth data to /api/plant-growth.
        
        Args:
            deviceId: Device ID (e.g., "pi-001")
            plantName: Plant name
            species: Plant species
            growthStage: Growth stage (e.g., "seedling", "vegetative", "flowering", "fruiting")
            healthStatus: Health status (e.g., "healthy", "stressed", "diseased")
            cameraDetections: Optional camera detection results
            timestamp: ISO format timestamp (auto-generated if not provided)
        
        Returns:
            bool: True if successful
        """
        payload = {
            "deviceId": deviceId,
            "plantName": plantName,
            "species": species,
            "growthStage": growthStage,
            "healthStatus": healthStatus,
            "cameraDetections": cameraDetections,
            "timestamp": timestamp or self._iso_timestamp()
        }
        return self._post("/api/plant-growth", payload)
    
    def send_ml_results(self,
                       deviceId: str,
                       detections: list,
                       health_score: int,
                       totalPlants: int,
                       avgConfidence: float,
                       timestamp: Optional[str] = None) -> bool:
        """
        Send ML detection results to /api/ml-results.
        
        Args:
            deviceId: Device ID (e.g., "pi-001")
            detections: List of detection dicts {plant_id, bbox, confidence, class_name, age_seconds}
            health_score: Overall health score (0-100)
            totalPlants: Total number of detected plants
            avgConfidence: Average confidence across detections
            timestamp: ISO format timestamp (auto-generated if not provided)
        
        Returns:
            bool: True if successful
        """
        payload = {
            "deviceId": deviceId,
            "timestamp": timestamp or self._iso_timestamp(),
            "detections": detections,
            "health_score": health_score,
            "totalPlants": totalPlants,
            "avgConfidence": avgConfidence
        }
        return self._post("/api/ml-results", payload)
    
    def send_control_ack(self,
                        deviceId: str,
                        action: str,
                        status: str,
                        timestamp: Optional[str] = None) -> bool:
        """
        Send device control acknowledgment (future use).
        
        Args:
            deviceId: Device ID
            action: Action executed (e.g., "pump_on", "light_dim")
            status: Status (e.g., "success", "failed")
            timestamp: ISO format timestamp
        
        Returns:
            bool: True if successful
        """
        payload = {
            "deviceId": deviceId,
            "action": action,
            "status": status,
            "timestamp": timestamp or self._iso_timestamp()
        }
        # Endpoint for control ack (if backend supports it)
        return self._post("/api/devices/control-ack", payload)
    
    @staticmethod
    def _iso_timestamp() -> str:
        """Get current timestamp in ISO format."""
        return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


# Example usage:
# client = BackendClient("http://localhost:8080", verbose=True)
# client.send_sensor_reading(22.5, 7.2, 85.0, 10.5, 800, 65.0, 24.0, 1013.5)
# client.send_ml_results("pi-001", [...detections...], 92, 1, 0.95)
