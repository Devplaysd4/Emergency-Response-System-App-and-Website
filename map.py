# import folium
# from folium.plugins import HeatMap

# # Create base map
# mapobj = folium.Map(
#     location=[26.1158, 91.7086],
#     zoom_start=6,
#     tiles=None,
#     zoom_control=True,
#     dragging=True
# )

# # Add OpenStreetMap as default
# folium.TileLayer('OpenStreetMap', name='OpenStreetMap').add_to(mapobj)

# # Add LayerControl
# folium.LayerControl(position='topright', collapsed=False).add_to(mapobj)

# # Heatmap data with normalized intensity (0–1)
# data = [
#     [26.1445, 91.7362, 0.77],
#     [26.2070, 92.9376, 0.46],
#     [27.1000, 93.6167, 0.82],
#     [27.5743, 95.8118, 0.91],
#     [26.1500, 94.2167, 0.63],
#     [25.5788, 91.8933, 0.55],
#     [25.5781, 91.8783, 0.48],
#     [25.5786, 91.8800, 0.72],
#     [25.5783, 91.8791, 0.61],
#     [25.6197, 93.7177, 0.84]
# ]

# # Add HeatMap
# HeatMap(data).add_to(mapobj)

# # Save map
# mapobj.save("folium_intro.html")
import folium
from folium.plugins import HeatMap

import json

# create a map object
mapObj = folium.Map(location=[26.1158, 91.7086], zoom_start=6)

# Load risk zones from JSON file
try:
    with open("website/risk_zones.json", "r") as f:
        risk_zones = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    risk_zones = []

# Format data for heatmap
data = [[float(zone['lat']), float(zone['lng']), float(zone['intensity'])] for zone in risk_zones]

# create heatmap from the data and add to map
if data:
    HeatMap(data).add_to(mapObj)

# save the map object as html
mapObj.save("output.html")