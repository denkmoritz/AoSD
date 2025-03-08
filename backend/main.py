from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import joblib
import os
import keras
import datetime
import pytz
import time
import threading
import geopandas as gpd
from shapely.geometry import Point

from scripts.kriging import load_tokyo_special_wards, perform_all_kriging
from scripts.live_fetch import fetch_all_data



LIVE_DATA_PATH = "data/live_no2_weather_data.csv"

app = FastAPI()

# ✅ Allow CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Load static data
print("📡 Loading Tokyo boundary data...")
tokyo_gdf = load_tokyo_special_wards()

# ✅ Load ML model & scaler with error handling
try:
    print("📡 Loading ML model and scaler...")
    scaler = joblib.load("data/scaler.pkl")
    model = keras.models.load_model("models/no2_forecast_model.keras")
    print("✅ ML Model and Scaler Loaded.")
except Exception as e:
    print(f"❌ Error loading ML model or scaler: {e}")
    scaler = None
    model = None

# ✅ Store latest predictions globally
latest_predictions = {}


def run_live_prediction():
    """Fetch live data, run model, update global predictions."""
    global latest_predictions

    print("📡 Fetching latest NO₂ & weather data...")
    fetch_all_data()  # ✅ Fetch new live data

    if not os.path.exists(LIVE_DATA_PATH):
        print("❌ Live data file not found.")
        return

    # ✅ Load latest data
    live_df = pd.read_csv(LIVE_DATA_PATH)

    # ✅ Rename columns to match training data
    rename_map = {
        'no2lag_1': 'NO2_lag_1',
        'no2lag_2': 'NO2_lag_2',
        'no2lag_3': 'NO2_lag_3',
        'no2lag_4': 'NO2_lag_4',
        'measurement_value': 'NO2_t'
    }
    live_df.rename(columns=rename_map, inplace=True)

    # ✅ Convert to GeoDataFrame
    live_df["geometry"] = live_df.apply(lambda row: Point(row["longitude"], row["latitude"]), axis=1)
    sensor_gdf = gpd.GeoDataFrame(live_df, geometry="geometry", crs="EPSG:4326")  # ✅ Set CRS to WGS84

    # ✅ Transform to UTM
    sensor_gdf = sensor_gdf.to_crs("EPSG:32654")  # ✅ Convert to Tokyo's UTM Zone

    # ✅ Check if ML model & scaler are available
    if not scaler or not model:
        print("❌ Error: ML model or scaler is not loaded. Cannot predict.")
        return

    # ✅ Check feature compatibility
    expected_features = scaler.feature_names_in_.tolist()
    missing_features = set(expected_features) - set(sensor_gdf.columns)

    if missing_features:
        print(f"🚨 ERROR: Missing features in live data: {missing_features}")
        return

    # ✅ Process data for model
    live_processed = sensor_gdf[expected_features].copy()  # 🔥 FIX: Explicitly copy data
    live_processed.fillna(live_processed.mean(), inplace=True)

    # ✅ Scale data
    live_scaled = pd.DataFrame(scaler.transform(live_processed), columns=expected_features)

    # ✅ Reshape for LSTM model
    X_live = live_scaled.values.reshape((live_scaled.shape[0], 1, live_scaled.shape[1]))

    # ✅ Predict next NO₂ values
    predictions = model.predict(X_live)

    # ✅ Store results
    sensor_gdf[['NO2_T+1', 'NO2_T+2', 'NO2_T+3', 'NO2_T+4']] = predictions
    sensor_gdf.to_csv(LIVE_DATA_PATH, index=False)
    print("✅ Predictions saved to live_predictions.csv")

    # ✅ Perform Kriging interpolation
    latest_predictions = perform_all_kriging(sensor_gdf, tokyo_gdf)  # 🔥 FIX: Use `sensor_gdf`
    print("✅ Live Kriging Interpolation Complete.")


@app.get("/pollution/live")
def get_live_pollution():
    """Serve the latest Kriging interpolated NO₂ data in lat/lon format."""
    if not latest_predictions:
        return {"status": "processing", "message": "Data is not ready yet. Try again later."}
    return latest_predictions


@app.post("/pollution/update")
def update_live_pollution(background_tasks: BackgroundTasks):
    """Manually trigger live data fetch & prediction."""
    background_tasks.add_task(run_live_prediction)
    return {"message": "Updating live data & predictions in the background..."}

@app.get("/pollution/timestamps")
def get_available_timestamps():
    """Generate dynamic timestamps for NO₂ predictions."""
    
    # ✅ Get the current Tokyo time
    now = datetime.datetime.now(pytz.timezone("Asia/Tokyo"))
    
    # ✅ Current timestamp (e.g., "14:36")
    current_time = now.strftime("%Y-%m-%d %H:%M")

    # ✅ Future timestamps (e.g., "15:00", "16:00", etc.)
    future_times = [
        (now + datetime.timedelta(hours=i)).replace(minute=0, second=0, microsecond=0).strftime("%Y-%m-%d %H:%M")
        for i in range(1, 5)  # Generate the next 4 full hours
    ]

    return {"timestamps": [current_time] + future_times}


# ✅ Auto-update at fixed times: 12:00, 13:00, 14:00, 15:00
def auto_update():
    while True:
        now = datetime.datetime.now(pytz.timezone("Asia/Tokyo"))
        next_update = now.replace(hour=now.hour + 1, minute=0, second=0, microsecond=0)

        print(f"⏳ Next update scheduled at: {next_update.strftime('%Y-%m-%d %H:%M:%S')}")

        time_until_update = (next_update - now).total_seconds()
        time.sleep(time_until_update)  # Wait until the next full hour

        run_live_prediction()  # ✅ Fetch & predict new data


@app.on_event("startup")
def startup_event():
    """Run live data fetch & prediction when FastAPI starts."""
    print("🚀 Running initial live data fetch and predictions...")
    threading.Thread(target=run_live_prediction, daemon=True).start()
    threading.Thread(target=auto_update, daemon=True).start()