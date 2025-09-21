import folium

# create a map object
mapObj = folium.Map(location=[26.1158, 91.7086], zoom_start=6)

# add a marker object to the map
folium.Marker(location=[27.2333, 94.1167]
              ).add_to(mapObj)
folium.Marker(location=[26.1445, 91.7362]
              ).add_to(mapObj)
folium.Marker(location=[26.3167, 91.0000]
              ).add_to(mapObj)

# save the map to a html file
mapObj.save('usermarkers.html')