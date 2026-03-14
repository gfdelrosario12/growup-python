import requests

class APIClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def send_ml_result(self, payload):
        try:
            response = requests.post(f"{self.base_url}/api/ml-results", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print("API Error:", e)
            return None

    def send_growth_record(self, payload):
        try:
            response = requests.post(f"{self.base_url}/api/plant-growth", json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print("API Error:", e)
            return None