import requests
import json
from datetime import datetime, timedelta
import os
from bs4 import BeautifulSoup # HTML parçalamak için
import re # Metin temizlemek için

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
    """Fetches astronomical events from In-The-Sky.org"""
    print("Fetching monthly events from In-The-Sky...")
    events = []
    today = datetime.now()
    day = today.day
    month = today.month
    year = today.year

    # 2. Takımyıldızlar (Constellations)
    try:
        c_url = f"https://in-the-sky.org/data/constellations.php?town=752850&day={day}&month={month}&year={year}"
        res = requests.get(c_url, timeout=10)
        soup = BeautifulSoup(res.content, 'html.parser')
        # 'Currently visible' olanları bul
        con_list = soup.find_all('a', href=re.compile(r'constellation\.php\?id='))
        if con_list:
            top_cons = [c.text for c in con_list[:3]] # İlk 3 takımyıldız
            events.append({
                "date": f"{day}",
                "month": f"{month}",
                "title": "Görünür Takımyıldızlar",
                "desc": f"Bu gece en iyi görülenler: {', '.join(top_cons)}."
            })
    except Exception as e:
        print(f"Takımyıldız verisi alınamadı: {e}")

    # Varsayılan (Eğer hiçbir şey çekilemezse boş kalmasın)
    if not events:
        events = [{"date": str(day), "month": "Oca", "title": "Gözlem Gecesi", "desc": "Gökyüzü haritasını kontrol etmeyi unutmayın."}]
        
    return events
    
def fetch_planets():
    """Fetches astronomical events from In-The-Sky.org"""
    print("Fetching monthly events from In-The-Sky...")
    events = []
    today = datetime.now()
    day = today.day
    month = today.month
    year = today.year

    # 1. Gezegen Görünürlüğü (Planets)
    try:
        p_url = f"https://in-the-sky.org/data/planets.php?town=752850&day={day}&month={month}&year={year}"
        res = requests.get(p_url, timeout=10)
        soup = BeautifulSoup(res.content, 'html.parser')
        # Sitedeki 'In the sky tonight' tablosunu bulmaya çalışıyoruz
        planet_table = soup.find('table', {'class': 'stripped'})
        if planet_table:
            rows = planet_table.find_all('tr')[1:4] # İlk 3 gezegeni al
            for row in rows:
                cols = row.find_all('td')
                if len(cols) > 1:
                    p_name = cols[0].text.strip()
                    p_info = cols[1].text.strip()
                    events.append({
                        "date": f"{day}",
                        "month": f"{month}", # Ay ismini dinamik yapabilirsiniz
                        "title": f"Gezegen: {p_name}",
                        "desc": f"{p_name} bu gece {p_info}."
                    })
    except Exception as e:
        print(f"Gezegen verisi alınamadı: {e}")

    # Varsayılan (Eğer hiçbir şey çekilemezse boş kalmasın)
    if not events:
        events = [{"date": str(day), "month": "Oca", "title": "Gözlem Gecesi", "desc": "Gökyüzü haritasını kontrol etmeyi unutmayın."}]
        
    return events

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
        "planets": fetch_planets(),
    }
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("data.json updated successfully.")

if __name__ == "__main__":
    update_json()



