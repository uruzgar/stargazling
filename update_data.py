import requests
import json
from datetime import datetime, timedelta
import os

# --- Configurations ---
LAT = "40.7806"
LON = "30.4033"

def fetch_weather():
    """Fetches real cloud cover data from Open-Meteo API"""
    print(f"Fetching real weather for {LAT}, {LON} from Open-Meteo...")
    
    # SDK yerine doğrudan URL isteği yapıyoruz (Daha hafif ve hatasız)
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "hourly": "cloud_cover", 
        "timezone": "auto",      
        "forecast_days": 2       
    }

    try:
        # Standart requests kütüphanesi kullanıyoruz
        response = requests.get(url, params=params)
        response.raise_for_status() 
        
        data = response.json()
        hourly_data = data.get("hourly", {})
        times = hourly_data.get("time", [])
        clouds = hourly_data.get("cloud_cover", [])

        weather_list = []
        
        now = datetime.now()
        
        for t_str, c_val in zip(times, clouds):
            dt_obj = datetime.strptime(t_str, "%Y-%m-%dT%H:%M")
            
            # Şu andan itibaren sonraki 12 saati al
            if now <= dt_obj < now + timedelta(hours=12):
                weather_list.append({
                    "hour": dt_obj.strftime("%H:%M"),
                    "cloud": c_val
                })
                
        return weather_list

    except Exception as e:
        print(f"Hata oluştu: {e}")
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
    # JSON dosyasının yolunu güvenli hale getiriyoruz
    base_path = os.path.dirname(os.path.realpath(__file__))
    json_path = os.path.join(base_path, "data.json")

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
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("data.json updated successfully.")

if __name__ == "__main__":
    update_json()

