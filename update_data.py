import requests
import json
from datetime import datetime, timedelta
import os

# --- Configurations ---
LAT = "40.76"
LON = "30.36"

# Additional imports for Skyfield
from skyfield.api import load, wgs84
from skyfield import almanac

def fetch_weather_timeline():
    """Fetches real hourly cloud cover, visibility, and humidity from Open-Meteo"""
    try:
        now = datetime.now()
        if now.hour < 12:
            start_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
            end_date = now.strftime("%Y-%m-%d")
        else:
            start_date = now.strftime("%Y-%m-%d")
            end_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
            
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": LAT,
            "longitude": LON,
            "hourly": "cloud_cover,visibility,relative_humidity_2m",
            "timezone": "auto",
            "start_date": start_date,
            "end_date": end_date
        }
        
        r = requests.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        clouds = hourly.get("cloud_cover", [])
        vis = hourly.get("visibility", [])
        hum = hourly.get("relative_humidity_2m", [])
        
        start_iso = f"{start_date}T18:00"
        final_timeline = []
        
        try:
            start_idx = times.index(start_iso)
            for i in range(13):
                if start_idx + i < len(times):
                    final_timeline.append({
                        "hour": datetime.fromisoformat(times[start_idx+i]).strftime("%H:%M"),
                        "cloud": clouds[start_idx+i],
                        "visibility": vis[start_idx+i],
                        "humidity": hum[start_idx+i]
                    })
        except ValueError:
            print(f"Warning: Start time {start_iso} not found in weather response")
            
        return final_timeline

    except Exception as e:
        print(f"Weather API Error: {e}")
        return []

def get_moon_phase_info():
    """Calculates Moon phase information for tonight"""
    try:
        eph = load('de421.bsp')
        ts = load.timescale()
        now = datetime.now().astimezone()
        t = ts.from_datetime(now)
        
        # 0 = New Moon, 0.25 = First Quarter, 0.5 = Full Moon, 0.75 = Last Quarter
        phase_angle = almanac.moon_phase(eph, t)
        percent = phase_angle.degrees
        
        # Convert degrees (0-360) to 0-1 phase and illumination
        # 180 degrees is Full Moon
        illumination = almanac.fraction_illuminated(eph, 'moon', t)
        
        phase_name = ""
        p = percent % 360
        if p < 22.5: phase_name = "Yeni Ay"
        elif p < 67.5: phase_name = "Hilal"
        elif p < 112.5: phase_name = "İlk Dördün"
        elif p < 157.5: phase_name = "Şişkin Ay"
        elif p < 202.5: phase_name = "Dolunay"
        elif p < 247.5: phase_name = "Şişkin Ay"
        elif p < 292.5: phase_name = "Son Dördün"
        else: phase_name = "Hilal (Son)"
        
        return {
            "name": phase_name,
            "illumination": round(illumination * 100),
            "angle": round(percent) 
        }
    except Exception as e:
        print(f"Moon Phase Error: {e}")
        return {"name": "--", "illumination": 0, "angle": 0}

def fetch_celestial_objects():
    """Calculates rise/set times & hourly altitude graph for objects"""
    objects_data = []
    
    try:
        eph = load('de421.bsp')
        sakarya_topo = wgs84.latlon(float(LAT), float(LON))
        ts = load.timescale()
        
        now = datetime.now()
        t0_dt = now.replace(hour=12, minute=0, second=0, microsecond=0).astimezone()
        t1_dt = (now + timedelta(days=1)).replace(hour=12, minute=0).astimezone()
        
        t0 = ts.from_datetime(t0_dt)
        t1 = ts.from_datetime(t1_dt)

        # Generate hourly timestamps for the graph (18:00 to 06:00)
        # Using the start date defined in fetch_weather_timeline logic ideally, but replicating simple logic here
        # We'll generate t objects for 18, 19... 06
        graph_times = []
        base_time = now if now.hour >= 12 else now - timedelta(days=1)
        base_time = base_time.replace(hour=18, minute=0, second=0, microsecond=0)
        
        for i in range(13):
            dt_hour = base_time + timedelta(hours=i)
            graph_times.append(ts.from_datetime(dt_hour.astimezone()))

        bodies = {
            'Güneş': eph['sun'],
            'Ay': eph['moon'],
            'Merkür': eph['mercury'],
            'Venüs': eph['venus'],
            'Mars': eph['mars'],
            'Jüpiter': eph['jupiter barycenter'],
            'Satürn': eph['saturn barycenter'],
        }

        for name, body in bodies.items():
            # 1. Rise/Set Times
            f = almanac.risings_and_settings(eph, body, sakarya_topo)
            t_events, events = almanac.find_discrete(t0, t1, f)
            
            rise_time = None
            set_time = None
            is_visible = False
            
            for time_obj, event in zip(t_events, events):
                dt = time_obj.astimezone(None)
                dt_str = dt.strftime("%H:%M")
                if event == 1: rise_time = dt_str
                else: set_time = dt_str
            
            if rise_time or set_time: is_visible = True
            
            # 2. Hourly Altitude Graph & Distance
            altitudes = []
            for t_g in graph_times:
                apparent = (eph['earth'] + sakarya_topo).at(t_g).observe(body).apparent()
                alt, az, dist = apparent.altaz()
                altitudes.append(round(alt.degrees, 1))
            
            # Distance at midnight (approx index 6)
            mid_apparent = (eph['earth'] + sakarya_topo).at(graph_times[6]).observe(body).apparent()
            _, _, dist_obj = mid_apparent.altaz()
            distance_km = f"{int(dist_obj.km):,}".replace(",", ".")

            objects_data.append({
                "name": name,
                "type": "planet" if name not in ['Güneş', 'Ay'] else ("star" if name == 'Güneş' else "moon"),
                "rise": rise_time if rise_time else "--:--",
                "set": set_time if set_time else "--:--",
                "visible": is_visible,
                "altitude_graph": altitudes,
                "distance_km": distance_km
            })

    except Exception as e:
        print(f"Skyfield General Error: {e}")
        return []

    return objects_data

def fetch_iss_passes():
    """Fetch ISS passes using Skyfield"""
    passes = []
    try:
        stations_url = 'http://celestrak.org/NORAD/elements/stations.txt'
        satellites = load.tle_file(stations_url)
        by_name = {sat.name: sat for sat in satellites}
        iss = by_name['ISS (ZARYA)']
        
        ts = load.timescale()
        now = datetime.now()
        t0 = ts.from_datetime(now.astimezone())
        t1 = ts.from_datetime((now + timedelta(days=1)).astimezone())
        
        sakarya_topos = wgs84.latlon(float(LAT), float(LON))
        
        t, events = iss.find_events(sakarya_topos, t0, t1, altitude_degrees=10.0)
        
        current_pass = {}
        for ti, event in zip(t, events):
            time_str = ti.astimezone(None).strftime("%H:%M")
            if event == 0: # Rise
                current_pass['start'] = time_str
            elif event == 1: # Culminate
                diff = (iss - sakarya_topos).at(ti)
                alt, az, distance = diff.altaz()
                current_pass['max_elev'] = int(alt.degrees)
            elif event == 2: # Set
                current_pass['end'] = time_str
                if 'start' in current_pass:
                    passes.append(current_pass)
                current_pass = {}
                
    except Exception as e:
        print(f"ISS/TLE Error: {e}")
        
    return passes

def check_meteor_showers():
    """Returns active meteor showers based on date"""
    now = datetime.now()
    # Simple static calendar check (can be refined)
    showers = [
        {"name": "Quadrantids", "start": (12, 28), "end": (1, 12), "peak": (1, 3)},
        {"name": "Lyrids", "start": (4, 14), "end": (4, 30), "peak": (4, 22)},
        {"name": "Eta Aquariids", "start": (4, 19), "end": (5, 28), "peak": (5, 6)},
        {"name": "Perseids", "start": (7, 17), "end": (8, 24), "peak": (8, 12)},
        {"name": "Orionids", "start": (10, 2), "end": (11, 7), "peak": (10, 21)},
        {"name": "Leonids", "start": (11, 6), "end": (11, 30), "peak": (11, 17)},
        {"name": "Geminids", "start": (12, 4), "end": (12, 17), "peak": (12, 14)},
    ]
    
    active = []
    current_md = (now.month, now.day)
    
    for s in showers:
        # Handle year wrap for ranges like Dec-Jan logic roughly
        if s["start"][0] == 12 and s["end"][0] == 1:
             in_range = (current_md >= s["start"]) or (current_md <= s["end"])
        else:
             in_range = s["start"] <= current_md <= s["end"]
             
        if in_range:
            active.append(s["name"])
            
    return active

def fetch_lists():
    return {
        "naked_eye": [
            {"name": "Jüpiter", "mag": -2.8},
            {"name": "Sirius", "mag": -1.4},
            {"name": "Pleiades (M45)", "mag": 1.6},
            {"name": "Andromeda (M31)", "mag": 3.4},
            {"name": "Betelgeuse", "mag": 0.5}
        ],
        "binocular": [
            {"name": "Orion Bulutsusu (M42)", "mag": 4.0},
            {"name": "Arı Kovanı (M44)", "mag": 3.7},
            {"name": "Herkül Kümesi (M13)", "mag": 5.8},
            {"name": "Çift Küme (NGC 869)", "mag": 3.7}
        ]
    }

def update_json():
    data = {
        "last_updated": datetime.now().isoformat(),
        "location": "Sakarya, Adapazarı",
        "timeline": {
            "start": "18:00",
            "end": "06:00"
        },
        "moon_phase": get_moon_phase_info(),
        "meteor_showers": check_meteor_showers(),
        "weather_hourly": fetch_weather_timeline(),
        "objects": fetch_celestial_objects(),
        "iss_passes": fetch_iss_passes(),
        "lists": fetch_lists()
    }
    
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("data.json updated successfully with advanced features.")

if __name__ == "__main__":
    update_json()
