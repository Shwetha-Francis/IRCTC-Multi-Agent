import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1]/ ".env")

BASE_URL = "http://api.railradar.in/v1"
API_KEY = os.getenv("RAILRADAR_API_KEY", "").strip()

print("Key loaded:", bool(API_KEY))
print("Key length:", len(API_KEY))


def railradar_get(endpoint, params=None):
    if not API_KEY:
        raise ValueError("RAILRADAR_API_KEY is missing from .env")

    response = requests.get(
        f"{BASE_URL}{endpoint}",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Accept": "application/json"
        },
        params=params,
        timeout=30
    )

    if not response.ok:
        print("Status code:", response.status_code)
        print("API error:", response.text)
        response.raise_for_status()


    return response.json()
def search_trains(source, destination, date=None):
    params = {"date":date} if date else None
    
    return railradar_get(
        f"/trains/between/{source}/{destination}",
        params
    )
    
# Search for a railway station by its name or code
def search_stations(query):
    return railradar_get(
        "/lookup/search/stations",
        {"q": query, "limit": 10}
    )
    
def get_train_details(train_number):
    return railradar_get(f"/trains/{train_number}")

def get_train_fare(
    train_number,date,source,destination,
    class_code="3A", quota_code="GN"
):
    return railradar_get(
        f"/trains/{train_number}/fare",
        {
            "journeyDate": date,
            "source": source,
            "destination": destination,
            "classCode": class_code,
            "quotaCode": quota_code
        }
    )
    
def get_live_tracking(train_number, date=None):
    params = {"date": date} if date else None
    
    return railradar_get(
        f"/trains/{train_number}/live",
        params
    )
    
if __name__ == "__main__":
    tests = [
        ("Train details", lambda: get_train_details("12952")),
        ("Train search", lambda: search_trains("NDLS", "MMCT", "2026-11-02")),
        ("Live tracking", lambda: get_live_tracking("12952")),
    ]

    for name, test in tests:
        print(f"\nTesting {name}...")
        try:
            result = test()
            print("Success:", result.get("success"))
        except requests.RequestException as error:
            print("Failed:", error)
        except ValueError as error:
            print("Failed:", error)