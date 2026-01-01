import requests
import json
from datetime import datetime
import os

# --- Configurations ---
LAT = "40.76"
LON = "30.36"
# In a real scenario, this script would crawl the sites. 
# For this demonstration, we simulate the scraping logic.

def fetch_weather():
    """Simulates fetching from Clear Outside"""
    # Note: Clear Outside often blocks generic scrapers, 
    # but in a GitHub Action, we can use specific headers or APIs.
    print(f"Fetching weather for {LAT}, {LON} from Clear Outside...")
    # Mock data structure updated for the 'current' day
    return [
        {"hour": "18:00", "cloud": 20},
        {"hour": "19:00", "cloud": 15},
        {"hour": "20:00", "cloud": 5},
        {"hour": "21:00", "cloud": 2},
        {"hour": "22:00", "cloud": 0},
        {"hour": "23:00", "cloud": 0},
        {"hour": "00:00", "cloud": 0},
        {"hour": "01:00", "cloud": 0},
        {"hour": "02:00", "cloud": 3},
        {"hour": "03:00", "cloud": 10}
    ]

def fetch_events():
    """Simulates fetching from Celestron/In-The-Sky"""
    print("Fetching monthly events...")
    return [
        {"date": "3-4", "month": "Oca", "title": "Quadrantid Meteor Yağmuru", "desc": "Yılın ilk büyük meteor yağmuru."},
        {"date": "10", "month": "Oca", "title": "Jüpiter Karşıtlığı", "desc": "Tüm gece en parlak haliyle görünür."},
        {"date": "19", "month": "Oca", "title": "Yeni Ay", "desc": "Gözlem için en karanlık gökyüzü."}
    ]

def update_json():
    data = {
        "last_updated": datetime.now().isoformat(),
        "location": "Sakarya, Adapazarı",
        "coordinates": f"{LAT}, {LON}",
        "weather": fetch_weather(),
        "events": fetch_events(),
        "planets": [
            {"name": "Jüpiter", "status": "Tüm gece görünür", "peak": "01:42", "badge": "Mükemmel", "class": "visible-high"},
            {"name": "Satürn", "status": "23:47'ye kadar", "peak": "19:10", "badge": "İyi", "class": "visible-mid"}
        ]
    }
    
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("data.json updated successfully.")

if __name__ == "__main__":
    update_json()
