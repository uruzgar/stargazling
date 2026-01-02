from skyfield.api import load, wgs84

def test_skyfield():
    print("Loading ephemeris...")
    eph = load('de421.bsp')
    print("Ephemeris keys:", eph.names())
    
    print("Trying earth lookup...")
    try:
        earth = eph['earth']
        print("Earth found:", earth)
    except Exception as e:
        print("Earth lookup failed:", e)

    print("Trying wgs84 latlon...")
    try:
        sakarya_topo = wgs84.latlon(40.76, 30.36)
        print("Topo created:", sakarya_topo)
    except Exception as e:
        print("Topo creation failed:", e)

    print("Trying addition...")
    try:
        observer = earth + sakarya_topo
        print("Addition successful:", observer)
    except Exception as e:
        print("Addition failed:", e)

if __name__ == "__main__":
    test_skyfield()
