import sys
import os
import requests
import time
import json
import datetime
import pytz
import pandas as pd

# Ensure the script can find config.py in the main directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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


def round_to_last_full_hour(dt):
    """Rounds the given datetime to the last full hour."""
    return dt.replace(minute=0, second=0, microsecond=0)


def fetch_current_no2(sensor_id):
    """Fetch the most recent NO₂ measurement from OpenAQ API."""
    enforce_rate_limit()

    url = f"https://api.openaq.org/v3/sensors/{sensor_id}/measurements"
    headers = {"X-API-Key": Config().api_key_openaq}
    params = {"order_by": "datetime", "sort": "desc", "limit": 1}

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json().get("results", [])
            return data[0].get("value") if data else None
    except Exception as e:
        print(f"Error fetching current NO₂ data: {e}")

    return None


def fetch_past_no2(sensor_id, timestamps_utc):
    """Fetch past 4 hourly NO₂ measurements from OpenAQ API."""
    url = f"https://api.openaq.org/v3/sensors/{sensor_id}/hours"
    headers = {"X-API-Key": Config().api_key_openaq}
    no2_data = {}

    for i, timestamp_utc in enumerate(timestamps_utc):
        enforce_rate_limit()

        datetime_from = (timestamp_utc - datetime.timedelta(hours=4)).astimezone(UTC_TZ)
        datetime_to = timestamp_utc.astimezone(UTC_TZ)

        params = {
            "datetime_from": datetime_from.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "datetime_to": datetime_to.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "limit": 5
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json().get("results", [])
                if data:
                    latest_entry = max(data, key=lambda x: x.get("datetime", ""))
                    no2_data[timestamp_utc.strftime("%Y-%m-%d %H:%M:%S UTC")] = latest_entry.get("value", None)
        except Exception as e:
            print(f"Error fetching past NO₂ data (t-{i + 1}): {e}")

    return no2_data


def estimate_t0(current_no2, past_values):
    """Estimate t-0 using t0 and past values (t-1 to t-4)."""
    all_values = [current_no2] + past_values
    valid_values = [v for v in all_values if v is not None]

    if len(valid_values) == 0:
        return None

    if len(valid_values) == 1:
        return valid_values[0]

    if len(valid_values) == 5:
        weights = [5, 4, 3, 2, 1]
        weighted_sum = sum(v * w for v, w in zip(valid_values, weights))
        return round(weighted_sum / sum(weights), 3)

    return round(sum(valid_values) / len(valid_values), 3)


def fetch_historical_weather(latitude, longitude, timestamp):
    """Fetch past 4 hours of weather data from OpenWeather API."""
    enforce_rate_limit()

    url = "https://history.openweathermap.org/data/2.5/history/city"
    timestamps_utc = [timestamp - datetime.timedelta(hours=i) for i in range(4, 0, -1)]
    start_unix = int(timestamps_utc[0].timestamp())
    end_unix = int(timestamps_utc[-1].timestamp())

    params = {
        "lat": latitude,
        "lon": longitude,
        "type": "hour",
        "start": start_unix,
        "end": end_unix,
        "appid": Config().api_key_openweather,
        "units": "metric"
    }

    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return {hour["dt"]: hour for hour in response.json().get("list", [])}
    except Exception as e:
        print(f"Error fetching historical weather data: {e}")

    return {}


def fetch_forecast_weather(latitude, longitude):
    """Fetch the next 4 hours of weather forecast from OpenWeather API."""
    enforce_rate_limit()

    url = f"https://pro.openweathermap.org/data/2.5/forecast/hourly?lat={latitude}&lon={longitude}&appid={Config().api_key_openweather}&units=metric"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            forecast_data = response.json().get("list", [])
            return {hour["dt"]: hour for hour in forecast_data[:4]}  # Take next 4 hours only
    except Exception as e:
        print(f"Error fetching forecast weather data: {e}")

    return {}

def fetch_all_data():
    """Fetch NO₂ and weather data for all stations."""
    try:
        with open("data/no2_sensors.json", "r", encoding="utf-8") as file:
            sensors_data = json.load(file)
    except FileNotFoundError:
        print("❌ Error: 'no2_sensors.json' file not found.")
        return

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

        timestamp_utc = round_to_last_full_hour(datetime.datetime.now(pytz.UTC))
        timestamp_tokyo = timestamp_utc.astimezone(TOKYO_TZ)
        past_timestamps_utc = [timestamp_utc - datetime.timedelta(hours=i) for i in range(1, 5)]
        future_timestamps_utc = [timestamp_utc + datetime.timedelta(hours=i) for i in range(1, 5)]

        # Fetch NO₂ Data
        current_no2 = fetch_current_no2(sensor_id)
        past_no2_values = fetch_past_no2(sensor_id, past_timestamps_utc)
        print(f"Fetched NO₂ values: {past_no2_values}")  # Debug print

        past_values = [past_no2_values.get(t.strftime("%Y-%m-%d %H:%M:%S UTC"), None) for t in past_timestamps_utc]
        print(f"Ordered past NO₂ values: {past_values}")  # Debug print

        estimated_t0 = estimate_t0(current_no2, past_values)

        # Fetch Weather Data
        weather_past = fetch_historical_weather(latitude, longitude, timestamp_utc)
        weather_future = fetch_forecast_weather(latitude, longitude)

        # Prepare Data Row
        row = {
            "station_id": station_id,
            "sensor_id": sensor_id,
            "latitude": latitude,
            "longitude": longitude,
            "measurement_value": estimated_t0,
            "measurement_datetime_utc": timestamp_utc.strftime("%Y-%m-%d %H:%M:%S"),
            "measurement_datetime_tokyo": timestamp_tokyo.strftime("%Y-%m-%d %H:%M:%S")
        }

        for i, val in enumerate(past_values, 1):
            row[f"no2lag_{i}"] = val

        # Add Past Weather Data
        for i, past_time in enumerate(past_timestamps_utc, 1):
            past_weather = weather_past.get(int(past_time.timestamp()), {})

            for var in ["temp", "humidity", "pressure"]:
                row[f"past_{var}_{i}"] = past_weather.get("main", {}).get(var)

            row[f"past_wind_{i}"] = past_weather.get("wind", {}).get("speed")
            row[f"past_wind_dir_{i}"] = past_weather.get("wind", {}).get("deg")

        # Add Future Weather Data
        for i, future_time in enumerate(future_timestamps_utc, 1):
            future_weather = weather_future.get(int(future_time.timestamp()), {})

            for var in ["temp", "humidity", "pressure"]:
                row[f"future_{var}_{i}"] = future_weather.get("main", {}).get(var)

            row[f"future_wind_{i}"] = future_weather.get("wind", {}).get("speed")
            row[f"future_wind_dir_{i}"] = future_weather.get("wind", {}).get("deg")

        # Append station data to list
        data_records.append(row)

    # Create DataFrame from all station data
    df = pd.DataFrame(data_records)

    # Save DataFrame
    df.to_csv("data/live_no2_weather_data.csv", index=False)
    print("data/live_no2_weather_data.csv")


if __name__ == "__main__":
    last_request_time = time.time()
    fetch_all_data()