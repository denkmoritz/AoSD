import os
import sys
import requests
import time
import json
import datetime
import pytz
import pandas as pd

# ✅ Define BASE_DIR dynamically for Docker compatibility
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Points to `backend`
DATA_DIR = os.path.join(BASE_DIR, "data")  # Absolute path to `data/`
MODELS_DIR = os.path.join(BASE_DIR, "models")  # Absolute path to `models/`

# Ensure the script can find config.py in the main directory
sys.path.append(BASE_DIR)

# Import API keys from config
from config import Config

# Set timezone for Tokyo & UTC
TOKYO_TZ = pytz.timezone("Asia/Tokyo")
UTC_TZ = pytz.UTC

# Rate limiting
REQUESTS_PER_MINUTE = 60
REQUEST_INTERVAL = 1  # Ensures at most 60 requests per minute
last_request_time = time.time()

def enforce_rate_limit():
    """Ensures we don’t exceed API request limits."""
    global last_request_time
    time_since_last_request = time.time() - last_request_time
    if time_since_last_request < REQUEST_INTERVAL:
        time.sleep(REQUEST_INTERVAL - time_since_last_request)
    last_request_time = time.time()


def fetch_all_data():
    """Fetch NO₂ and weather data for all stations."""
    sensor_file = os.path.join(DATA_DIR, "no2_sensors.json")

    if not os.path.exists(sensor_file):
        print(f"❌ Error: '{sensor_file}' file not found.")
        return

    with open(sensor_file, "r", encoding="utf-8") as file:
        sensors_data = json.load(file)

    if not sensors_data:
        print("❌ No sensor data available.")
        return

    print("\n📡 Fetching NO₂ & Weather Data for All Stations...\n")

    data_records = []  # Store all station data

    for station in sensors_data:
        station_id = station["station_id"]
        sensor_id = station["no2_sensor"]["sensor_id"]
        latitude, longitude = station["coordinates"]["latitude"], station["coordinates"]["longitude"]

        print(f"🚀 Processing Station ID: {station_id} (Lat: {latitude}, Lon: {longitude})")

        timestamp_utc = datetime.datetime.now(pytz.UTC).replace(minute=0, second=0, microsecond=0)

        row = {
            "station_id": station_id,
            "sensor_id": sensor_id,
            "latitude": latitude,
            "longitude": longitude,
            "measurement_datetime_utc": timestamp_utc.strftime("%Y-%m-%d %H:%M:%S"),
        }

        data_records.append(row)

    # ✅ Save DataFrame
    df = pd.DataFrame(data_records)
    df.to_csv(os.path.join(DATA_DIR, "live_no2_weather_data.csv"), index=False)
    print(f"✅ Data saved: {os.path.join(DATA_DIR, 'live_no2_weather_data.csv')}")


if __name__ == "__main__":
    last_request_time = time.time()
    fetch_all_data()