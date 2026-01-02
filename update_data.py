import requests
import json
from datetime import datetime, timedelta
import os
import openmeteo_requests

import pandas as pd
import requests_cache
from retry_requests import retry

# --- Configurations ---
LAT = "40.76"
LON = "30.36"

def fetch_weather():
"""Fetches real cloud cover data from Open-Meteo API"""
    print(f"Fetching real weather for {LAT}, {LON} from Open-Meteo...")
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": "cloud_cover", # Saatlik bulut verisi
        "timezone": "auto",      # Konumun saat dilimini otomatik algıla
        "forecast_days": 2       # Bugün ve yarını al (gece yarısını geçtiği için)
    }

    try:
        #response = requests.get(url, params=params)
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]
        #response.raise_for_status() # Hata varsa durdur
        
        data = response.json()
        hourly_data = data.get("hourly", {})
        times = hourly_data.get("time", [])
        clouds = hourly_data.get("cloud_cover", [])

        weather_list = []
        
        # Şu anki saati al
        now = datetime.now()
        
        # Gelen veriyi işle
        for t_str, c_val in zip(times, clouds):
            # API'den gelen zaman formatı: "2023-10-27T14:00"
            dt_obj = datetime.strptime(t_str, "%Y-%m-%dT%H:%M")
            
            # Sadece şu andan itibaren sonraki 12 saati al (Gözlem için)
            if now <= dt_obj < now + timedelta(hours=12):
                weather_list.append({
                    "hour": dt_obj.strftime("%H:%M"), # "18:00" formatına çevir
                    "cloud": c_val # Yüzde olarak bulut oranı (0-100)
                })
                
        return weather_list

    except Exception as e:
        print(f"Hata oluştu: {e}")
        # Hata durumunda boş liste veya varsayılan değer dön
        return []

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

