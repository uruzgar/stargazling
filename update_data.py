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

    aylar = {1: "Oca", 2: "Şub", 3: "Mar", 4: "Nis", 5: "May", 6: "Haz", 
             7: "Tem", 8: "Ağu", 9: "Eyl", 10: "Eki", 11: "Kas", 12: "Ara"}
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
    aylar = {1: "Oca", 2: "Şub", 3: "Mar", 4: "Nis", 5: "May", 6: "Haz", 
             7: "Tem", 8: "Ağu", 9: "Eyl", 10: "Eki", 11: "Kas", 12: "Ara"}
    events = []
    today = datetime.now()
    day = today.day
    month = today.month
    year = today.year

    c_url = f"https://in-the-sky.org/data/constellations.php?town=752850&day={day}&month={month}&year={year}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    # 2. Takımyıldızlar (Constellations)
    try:
        
        res = requests.get(c_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.content, 'html.parser')
        # Olay kartlarını bul (genellikle 'newsitem' class'ı kullanılır)
        items = soup.find_all('div', {'class': 'newsitem'})
        
        for item in items:
            # Tarih kısmını ayıkla (Örn: "02 Jan 2026")
            date_div = item.find('div', {'class': 'date'})
            if date_div:
                date_text = date_div.text.strip()
                
                # Sadece BUGÜN olan olayları filtrele
                # Sitedeki format genelde "02 Jan" şeklindedir
                if date_text.startswith(day_str):
                    title_elem = item.find('a')
                    desc_elem = item.find('div', {'class': 'newsitem_text'})
                    
                    if title_elem:
                        title = title_elem.text.strip()
                        desc = desc_elem.text.strip() if desc_elem else "Detaylı bilgi bulunmuyor."
                        
                        # Başlığı Türkçeye çevirme (Basit denemeler)
                        title = title.replace("Conjunction", "Yakınlaşma")
                        title = title.replace("Moon", "Ay").replace("Close approach", "Yakın geçiş")
                        
                        events.append({
                            "date": day_str,
                            "month": current_month_tr,
                            "title": title,
                            "desc": desc[:150] + "..." # Özeti kısa tutalım
                        })
                        
    except Exception as e:
        print(f"Olaylar çekilirken hata oluştu: {e}")

    # Eğer bugün bir olay yoksa boş dönmesin, genel bilgi versin
    if not events:
        events.append({
            "date": day_str,
            "month": current_month_tr,
            "title": "Sakin Gökyüzü",
            "desc": "Bu gece için özel bir gök olayı kaydedilmedi. Gözlem için harika bir gece olabilir!"
        })
        
    return events
    
def fetch_planets():
    """Gezegen verilerini Sakarya konumu için çeker"""
    print("Gezegen verileri çekiliyor...")
    aylar = {1: "Oca", 2: "Şub", 3: "Mar", 4: "Nis", 5: "May", 6: "Haz", 
             7: "Tem", 8: "Ağu", 9: "Eyl", 10: "Eki", 11: "Kas", 12: "Ara"}
    events = []
    today = datetime.now()
    day = today.day
    month = today.month
    year = today.year

    p_url = f"https://in-the-sky.org/data/planets.php?town=752850&day={day}&month={month}&year={year}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    # 1. Gezegen Görünürlüğü (Planets)
    try:
        res = requests.get(p_url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.content, 'html.parser')
        # Sitedeki 'In the sky tonight' tablosunu bulmaya çalışıyoruz
        #planet_table = soup.find('table', {'class': 'stripped'})
        table = soup.find('table', {'class': 'stripped'})
        if table:
            rows = table.find_all('tr')[1:] # Başlığı atla
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    name_en = cols[0].text.strip()
                    status = cols[1].text.strip()
                                           
                        # Görünürlük durumuna göre CSS class ataması
                        v_class = "visible-high" if "visible" in status.lower() else "visible-low"
                        
                        planets_data.append({
                            "name": name_en,
                            "status": status,
                            "class": v_class
                        })
            
    except Exception as e:
        print(f"Gezegen verisi alınamadı: {e}")

    # Varsayılan (Eğer hiçbir şey çekilemezse boş kalmasın)
    if not events:
        events = [{"date": str(day), "month": str(aylar[today.month]), "title": "Gözlem Gecesi", "desc": "Gökyüzü haritasını kontrol etmeyi unutmayın."}]
        
    return events

def fetch_deepsky():
    """Fetches deep sky objects (DSO) from In-The-Sky.org"""
    print("Fetching deep sky objects...")
    aylar = {1: "Oca", 2: "Şub", 3: "Mar", 4: "Nis", 5: "May", 6: "Haz", 
             7: "Tem", 8: "Ağu", 9: "Eyl", 10: "Eki", 11: "Kas", 12: "Ara"}
    dso_list = []
    today = datetime.now()
    day = today.day
    month = today.month
    year = today.year
    # Sakarya konumu için özelleştirilmiş URL
    url = f"https://in-the-sky.org/data/deepsky.php?town=752850&day={day}&month={month}&year={year}"
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        res = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(res.content, 'html.parser')
        
        # Sitedeki ana veri tablosunu bul
        table = soup.find('table', {'class': 'planetinfo centred'})
        if table:
            rows = table.find_all('tr')[1:6]  # Başlık hariç ilk 5 objeyi al
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 4:
                    name = cols[1].text.strip() # Obje Adı (Örn: M31)
                    obj_type = cols[2].text.strip() # Tür (Örn: Galaxy)
                    mag = cols[3].text.strip() # Parlaklık
                    
                    dso_list.append({
                        "name": name,
                        "type": obj_type,
                        "magnitude": mag,
                        "desc": f"{obj_type} türünde, {mag} parlaklığında."
                    })
    except Exception as e:
        print(f"Deep Sky verisi alınamadı: {e}")
    
    return dso_list

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
        "planets": fetch_planets()
    }
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("data.json updated successfully.")

if __name__ == "__main__":
    update_json()










