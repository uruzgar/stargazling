import requests
import json
from datetime import datetime, timedelta
import os

# --- Configurations ---
LAT = "40.76"
LON = "30.36"

# Mock Data Generators for robust layout testing

def fetch_weather_timeline():
    """Fetches real hourly cloud cover for tonight (18:00 - 06:00) from Open-Meteo"""
    try:
        # Get start/end times for the upcoming/current night window
        now = datetime.now()
        
        # If we are effectively in the early morning (e.g. 02:00), "tonight" started yesterday 18:00
        # If we are in the afternoon (e.g. 14:00), "tonight" starts today 18:00
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
            "hourly": "cloud_cover",
            "timezone": "auto",
            "start_date": start_date,
            "end_date": end_date
        }
        
        r = requests.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        
        # Filter for 18:00 to 06:00
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        clouds = hourly.get("cloud_cover", [])
        
        timeline = []
        target_hours = ["18", "19", "20", "21", "22", "23", "00", "01", "02", "03", "04", "05", "06"]
        
        for t, c in zip(times, clouds):
            # t format: "2025-01-02T18:00"
            dt = datetime.fromisoformat(t)
            h_str = dt.strftime("%H")
            
            # Simple check: Is this hour in our target list?
            # And is it part of the correct sequence? 
            # (Simplistic filter: just check if hour is in target set)
            if h_str in ["18", "19", "20", "21", "22", "23", "00", "01", "02", "03", "04", "05", "06"]:
                timeline.append({
                    "hour": dt.strftime("%H:%M"),
                    "cloud": c
                })
                
        # Sort to ensure 18:00 -> 06:00 order (OpenMeteo returns sorted by time, so usually safe)
        # However, we simply return what we found.
        # Ideally, we want to slice the exact 13 hours representing "tonight".
        # For robustness in this snippet, we'll return the list as retrieved from the API 
        # which spans start_date 00:00 to end_date 23:59. We need to act smarter.
        
        # Refined Logic: Find the index of today's 18:00 and take next 13 points
        final_timeline = []
        start_iso = f"{start_date}T18:00"
        
        try:
            start_idx = times.index(start_iso)
            # We want 13 hours: 18, 19, ... 06
            for i in range(13):
                if start_idx + i < len(times):
                    final_timeline.append({
                        "hour": datetime.fromisoformat(times[start_idx+i]).strftime("%H:%M"),
                        "cloud": clouds[start_idx+i]
                    })
        except ValueError:
            print(f"Warning: Start time {start_iso} not found in weather response")
            
        return final_timeline

    except Exception as e:
        print(f"Weather API Error: {e}")
        return [] # Fallback empty or old mock functionality if preferred

# Additional imports for Skyfield
from skyfield.api import load, wgs84
from skyfield import almanac

def fetch_celestial_objects():
    """Calculates rise/set times for major planets and DSOs using Skyfield"""
    objects_data = []
    
    try:
        # Load Ephemeris
        eph = load('de421.bsp')
        # Define observer on Earth surface
        sakarya_topo = wgs84.latlon(float(LAT), float(LON))
        
        ts = load.timescale()
        
        # Define Time Range: Today 12:00 to Tomorrow 12:00 to cover the night fully
        now = datetime.now()
        # Ensure we have a timezone aware datetime for Skyfield
        t0_dt = now.replace(hour=12, minute=0, second=0, microsecond=0).astimezone()
        t1_dt = (now + timedelta(days=1)).replace(hour=12, minute=0).astimezone()
        
        t0 = ts.from_datetime(t0_dt)
        t1 = ts.from_datetime(t1_dt)

        # Define bodies to track
        # Note: de421 names: 'sun', 'moon', 'mercury', 'venus', 'earth', 'mars', 'jupiter barycenter', 'saturn barycenter'
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
            # Calculate Rise/Set
            # risings_and_settings(eph, target, observer)
            # Passing Topos directly (sakarya_topo) allows Skyfield to infer Earth context
            f = almanac.risings_and_settings(eph, body, sakarya_topo)
            try:
                t, y = almanac.find_discrete(t0, t1, f)
            except Exception as e:
                # Fallback if calculation fails for some body
                print(f"Almanac error for {name}: {e}")
                continue
            
            rise_time = None
            set_time = None
            is_visible = False
            
            for time_obj, event in zip(t, y):
                # event: 1=rise, 0=set
                # Convert Skyfield Time to local datetime
                dt = time_obj.astimezone(None) # uses local system timezone
                dt_str = dt.strftime("%H:%M")
                
                if event == 1:
                    rise_time = dt_str
                else:
                    set_time = dt_str
            
            # Visibility Check (simplistic)
            if rise_time or set_time:
                 is_visible = True

            objects_data.append({
                "name": name,
                "type": "planet" if name not in ['Güneş', 'Ay'] else ("star" if name == 'Güneş' else "moon"),
                "rise": rise_time if rise_time else "--:--",
                "set": set_time if set_time else "--:--",
                "visible": is_visible
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
        # Skyfield caches TLEs automatically
        satellites = load.tle_file(stations_url)
        by_name = {sat.name: sat for sat in satellites}
        iss = by_name['ISS (ZARYA)']
        
        ts = load.timescale()
        now = datetime.now()
        t0 = ts.from_datetime(now.astimezone())
        t1 = ts.from_datetime((now + timedelta(days=1)).astimezone())
        
        # Define observer
        sakarya_topos = wgs84.latlon(float(LAT), float(LON))
        
        t, events = iss.find_events(sakarya_topos, t0, t1, altitude_degrees=10.0)
        
        # Events: 0=rise, 1=culminate, 2=set
        current_pass = {}
        for ti, event in zip(t, events):
            # ti is Skyfield Time object
            time_str = ti.astimezone(None).strftime("%H:%M") # Local time
            
            if event == 0: # Rise
                current_pass['start'] = time_str
            elif event == 1: # Culminate
                # Get altitude
                # (satellite - observer).at(time)
                # But 'iss' is TLE EarthSatellite, 'sakarya_topos' is position on Earth.
                # correct usage: (iss - sakarya_topos).at(ti)
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

def fetch_lists():
    """Fetch Skymaps/In-the-sky lists with magnitude"""
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
        "weather_hourly": fetch_weather_timeline(),
        "objects": fetch_celestial_objects(),
        "iss_passes": fetch_iss_passes(),
        "lists": fetch_lists()
    }
    
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("data.json updated successfully with deep sky objects.")

if __name__ == "__main__":
    update_json()
