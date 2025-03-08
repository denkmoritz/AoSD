import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from pykrige.ok import OrdinaryKriging
from pyproj import Transformer

# ✅ Define CRS
UTM_ZONE = "EPSG:32654"  # Tokyo UTM Zone
GEOGRAPHIC_CRS = "EPSG:4326"  # WGS84 Lat/Lon

# ✅ Define transformer to convert UTM (EPSG:32654) → WGS84 (EPSG:4326)
transformer = Transformer.from_crs(UTM_ZONE, GEOGRAPHIC_CRS, always_xy=True)

def transform_utm_to_geographic(points):
    """Convert UTM coordinates (X, Y) back to geographic coordinates (lat, lon)."""
    lons, lats = transformer.transform([p[0] for p in points], [p[1] for p in points])
    return list(zip(lats, lons))  # ✅ Return (lat, lon) pairs


# ✅ Load Tokyo boundary data in UTM
def load_tokyo_special_wards(filepath="data/tokyo_special_ward_topo.json"):
    special_wards_gdf = gpd.read_file(filepath)
    if special_wards_gdf.crs is None:
        special_wards_gdf.set_crs(epsg=4326, inplace=True)
    return special_wards_gdf.to_crs(UTM_ZONE)  # ✅ Keep in UTM


# ✅ Load live NO₂ predictions in UTM
def load_live_predictions(filepath="data/live_predictions.csv"):
    df = pd.read_csv(filepath)
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs=GEOGRAPHIC_CRS)
    return gdf.to_crs(UTM_ZONE)  # ✅ Convert to UTM only once


def perform_all_kriging(sensor_df, tokyo_gdf):
    """Performs Kriging for NO₂ concentration in UTM coordinates, then converts to lat/lon."""

    best_variogram = "gaussian"
    best_range = 10000
    best_nugget = 1

    # ✅ Get spatial bounds from Tokyo UTM map
    minx, miny, maxx, maxy = tokyo_gdf.total_bounds

    # ✅ Create a uniform grid in UTM coordinates
    grid_x = np.linspace(minx, maxx, 50)  # UTM X (Longitude)
    grid_y = np.linspace(miny, maxy, 50)  # UTM Y (Latitude)

    interpolations = {}

    for column in ["NO2_t", "NO2_T+1", "NO2_T+2", "NO2_T+3", "NO2_T+4"]:
        # ✅ Ensure sensor data remains in UTM
        sensor_gdf = sensor_df.copy()

        # ✅ Extract UTM X, Y, and NO₂ values
        sensor_x = sensor_gdf.geometry.x.values  # UTM X
        sensor_y = sensor_gdf.geometry.y.values  # UTM Y
        sensor_values = sensor_df[column].values  # NO₂ Concentrations

        # ✅ Perform Kriging
        OK = OrdinaryKriging(
            sensor_x, sensor_y, sensor_values,
            variogram_model=best_variogram,
            variogram_parameters={"sill": np.var(sensor_values), "range": best_range, "nugget": best_nugget},
            nlags=20, weight=True
        )

        z_kriged, _ = OK.execute("grid", grid_x, grid_y)

        # ✅ Store interpolated results where inside Tokyo boundary
        heatmap_data = []
        utm_points = []

        for i, x in enumerate(grid_x):
            for j, y in enumerate(grid_y):
                point = Point(x, y)
                if tokyo_gdf.geometry.contains(point).any():  # ✅ Filter inside Tokyo
                    z_value = float(z_kriged[j, i])  # ✅ Ensure float values

                    if not np.isnan(z_value):  # ✅ Remove NaNs
                        utm_points.append((x, y, z_value))

        # ✅ Convert UTM points to Lat/Lon
        lat_lon_points = transform_utm_to_geographic([(p[0], p[1]) for p in utm_points])
        heatmap_data = [[lat, lon, val] for (lat, lon), (_, _, val) in zip(lat_lon_points, utm_points)]

        interpolations[column] = heatmap_data  # ✅ Now data is in (lat, lon, value) format

    return interpolations  # ✅ Returns correctly formatted data