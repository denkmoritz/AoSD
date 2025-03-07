import json
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx  # ✅ Add basemap for better visualization

# ✅ File paths
sensor_file = "backend/data/no2_sensors.json"
boundary_file = "backend/data/tokyo_special_ward_topo.json"

# ✅ Load NO₂ sensor data
with open(sensor_file, "r", encoding="utf-8") as f:
    sensor_data = json.load(f)

# ✅ Extract sensor locations
sensor_lats = [station["coordinates"]["latitude"] for station in sensor_data]
sensor_lons = [station["coordinates"]["longitude"] for station in sensor_data]

# ✅ Load Tokyo special wards boundary
tokyo_gdf = gpd.read_file(boundary_file)
if tokyo_gdf.crs is None:
    tokyo_gdf.set_crs(epsg=4326, inplace=True)

# ✅ Convert CRS to Web Mercator (3857) for basemap support
tokyo_gdf = tokyo_gdf.to_crs(epsg=3857)

# ✅ Convert sensor locations to GeoDataFrame
sensor_gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy(sensor_lons, sensor_lats), crs="EPSG:4326")
sensor_gdf = sensor_gdf.to_crs(epsg=3857)  # Convert to Web Mercator

# ✅ Create the figure
fig, ax = plt.subplots(figsize=(10, 8))

# ✅ Plot Tokyo special wards boundary
tokyo_gdf.boundary.plot(ax=ax, color="black", linewidth=1, label="Tokyo Special Wards")

# ✅ Plot NO₂ monitoring stations with better visualization
sensor_gdf.plot(ax=ax, markersize=50, color="red", edgecolor="black", alpha=0.7, label="NO₂ Monitoring Stations")

# ✅ Add a basemap for context
ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik)

# ✅ Customize plot appearance
ax.legend()
ax.set_title("NO₂ Monitoring Stations in Tokyo Special Wards", fontsize=14, fontweight="bold")
ax.set_xlabel("Longitude", fontsize=12)
ax.set_ylabel("Latitude", fontsize=12)

plt.savefig("frontend/public/no2_station_map.png", dpi = 600)