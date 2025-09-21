import platform
import geocoder
from plyer import gps

class Location:
    def __init__(self, lat, lon):
        self.latitude = lat
        self.longitude = lon

def get_location():
    if platform.system() == 'Windows':
        try:
            g = geocoder.ip('me')
            if g.ok:
                return Location(g.latlng[0], g.latlng[1])
            else:
                return None
        except Exception as e:
            print(f"Error getting location with geocoder: {e}")
            return None
    else:
        try:
            # This is a blocking call on some platforms, but not all.
            # On Android, it returns the last known location immediately.
            # To get a real-time location, we would need to use callbacks.
            # For the purpose of this fix, we will rely on the last known location.
            location = gps.get_location()
            if location:
                return Location(location['lat'], location['lon'])
            return None
        except Exception as e:
            print(f"Error getting location with plyer.gps: {e}")
            return None
