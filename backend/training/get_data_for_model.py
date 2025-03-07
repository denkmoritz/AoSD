import requests
import csv
import datetime
import time
import pytz
import json
import random
from config import Config

# Constants for API rate limits
MAX_CALLS_PER_MINUTE = 60
MAX_CALLS_PER_HOUR = 2000
RATE_LIMIT_SLEEP = 1

# Set up time range for random timestamp selection
START_DATE = datetime.datetime(2024, 7, 1, 0, 0, 0, tzinfo=pytz.UTC)
END_DATE = datetime.datetime(2025, 2, 28, 23, 0, 0, tzinfo=pytz.UTC)

# Target number of unique timestamps
TARGET_TIMESTAMPS = 100

# Timezone for Tokyo
TOKYO_TZ = pytz.timezone("Asia/Tokyo")


def generate_random_timestamp(existing_timestamps):
    """Generate a unique timestamp between July 1, 2024, and February 28, 2025."""
    while True:
        random_time_utc = START_DATE + datetime.timedelta(
            seconds=random.randint(0, int((END_DATE - START_DATE).total_seconds()))
        )
        random_time_utc = random_time_utc.replace(minute=0, second=0, microsecond=0)

        timestamp_str = random_time_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Ensure uniqueness
        if timestamp_str not in existing_timestamps:
            existing_timestamps.add(timestamp_str)
            return random_time_utc


def fetch_no2_measurement(sensor_id, timestamps):
    """Fetch NO₂ data from OpenAQ API for the past 4 hours and the main timestamp."""
    url = f"https://api.openaq.org/v3/sensors/{sensor_id}/hours"
    headers = {"X-API-Key": Config().api_key_openaq}

    no2_values = []
    for timestamp in timestamps:
        target_dt = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.UTC)
        datetime_from = (target_dt - datetime.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        datetime_to = target_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        params = {"datetime_from": datetime_from, "datetime_to": datetime_to, "limit": 1}

        try:
            response = requests.get(url, headers=headers, params=params)
            time.sleep(RATE_LIMIT_SLEEP)  # Respect API rate limit

            if response.status_code == 200:
                data = response.json().get("results", [])
                no2_values.append(data[0].get("value") if data else None)
            else:
                print(f"❌ OpenAQ API Error: {response.status_code} - {response.text}")
                no2_values.append(None)
        except Exception as e:
            print(f"❌ Error fetching NO₂ data: {e}")
            no2_values.append(None)

    return no2_values


def fetch_historical_weather(latitude, longitude, target_utc):
    """Fetch historical weather data from OpenWeather API for a range of timestamps (past 4, main, future 4 hours)."""
    url = "https://history.openweathermap.org/data/2.5/history/city"
    timestamps_utc = [target_utc - datetime.timedelta(hours=i) for i in range(4, 0, -1)] + \
                     [target_utc] + \
                     [target_utc + datetime.timedelta(hours=i) for i in range(1, 5)]

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
        time.sleep(0.5)  # Avoid rate limit

        if response.status_code == 200:
            weather_data = response.json().get("list", [])
            return {hour["dt"]: hour for hour in weather_data}
        else:
            print(f"⚠️ OpenWeather API Error: {response.status_code} - {response.text}")
            return {}
    except Exception as e:
        print(f"❌ Error fetching weather data: {e}")
        return {}


def save_data_to_csv(record, filename="data/new_data_for_model.csv"):
    """Store collected data into a CSV file."""
    fieldnames = record.keys()

    # Check if the file exists, if not, write the header
    write_header = False
    try:
        with open(filename, "r", encoding="utf-8") as f:
            if not f.readline():
                write_header = True
    except FileNotFoundError:
        write_header = True

    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(record)


def main():
    """Main function to fetch NO₂ and weather data for random timestamps."""
    with open("data/no2_sensors.json", "r", encoding="utf-8") as file:
        sensors_data = json.load(file)

    collected_timestamps = set()

    while len(collected_timestamps) < TARGET_TIMESTAMPS:
        timestamp_utc = generate_random_timestamp(collected_timestamps)
        timestamp_tokyo = timestamp_utc.astimezone(TOKYO_TZ)  # Convert to Tokyo time
        timestamps_utc = [timestamp_utc - datetime.timedelta(hours=i) for i in range(4, 0, -1)] + \
                         [timestamp_utc] + \
                         [timestamp_utc + datetime.timedelta(hours=i) for i in range(1, 5)]
        timestamps_str = [t.strftime("%Y-%m-%dT%H:%M:%SZ") for t in timestamps_utc]

        for station in sensors_data:
            station_id = station["station_id"]
            sensor_id = station["no2_sensor"]["sensor_id"]
            latitude, longitude = station["coordinates"]["latitude"], station["coordinates"]["longitude"]

            no2_values = fetch_no2_measurement(sensor_id, timestamps_str[:5])
            weather_data = fetch_historical_weather(latitude, longitude, timestamp_utc)

            record = {
                "station_id": station_id,
                "sensor_id": sensor_id,
                "latitude": latitude,
                "longitude": longitude,
                "measurement_value": no2_values[4],
                "measurement_datetime_utc": timestamp_utc.strftime("%Y-%m-%d %H:%M:%S"),
                "measurement_datetime_tokyo": timestamp_tokyo.strftime("%Y-%m-%d %H:%M:%S"),
            }

            for i in range(4):
                record[f"NO2_lag_{i+1}"] = no2_values[i] if i < len(no2_values) else None
                past_weather = weather_data.get(int(timestamps_utc[i].timestamp()), {})
                future_weather = weather_data.get(int(timestamps_utc[5 + i].timestamp()), {})

                record[f"past_temp_{i+1}"] = past_weather.get("main", {}).get("temp")
                record[f"past_wind_{i+1}"] = past_weather.get("wind", {}).get("speed")
                record[f"past_wind_dir_{i+1}"] = past_weather.get("wind", {}).get("deg")
                record[f"past_humidity_{i+1}"] = past_weather.get("main", {}).get("humidity")
                record[f"past_pressure_{i+1}"] = past_weather.get("main", {}).get("pressure")

                record[f"future_temp_{i+1}"] = future_weather.get("main", {}).get("temp")
                record[f"future_wind_{i+1}"] = future_weather.get("wind", {}).get("speed")
                record[f"future_wind_dir_{i+1}"] = future_weather.get("wind", {}).get("deg")
                record[f"future_humidity_{i+1}"] = future_weather.get("main", {}).get("humidity")
                record[f"future_pressure_{i+1}"] = future_weather.get("main", {}).get("pressure")

            print(f"📝 Storing record ({len(collected_timestamps)}/100):", record)
            save_data_to_csv(record)
            time.sleep(RATE_LIMIT_SLEEP)  # Avoid exceeding rate limits


if __name__ == "__main__":
    main()