import pandas as pd
import numpy as np
import os
import keras
from keras import layers
import joblib

# Paths
DATA_DIR = "data/"
MODEL_DIR = "models/"

# Load preprocessed data
train_df = pd.read_csv(os.path.join(DATA_DIR, "train_preprocessed.csv"))

# Drop metadata columns that are not needed for training
metadata_cols = ["station_id", "sensor_id", "latitude", "longitude", "measurement_datetime_utc", "measurement_datetime_tokyo"]
train_df = train_df.drop(columns=[col for col in metadata_cols if col in train_df.columns], errors="ignore")

# Load the scaler to ensure correct feature ordering
scaler = joblib.load(os.path.join(DATA_DIR, "scaler.pkl"))
input_features = scaler.feature_names_in_.tolist()  # Ensure we use the same features as in preprocessing

# Define target columns (NO₂ predictions for next 4 hours)
target_cols = [f'NO2_target_T+{i}' for i in range(1, 5)]

# Ensure only features used in preprocessing are included
feature_cols = [col for col in input_features if col in train_df.columns]

# **Ensure no missing features**
missing_features = set(input_features) - set(train_df.columns)
extra_features = set(train_df.columns) - set(input_features) - set(target_cols)

if missing_features:
    print(f"⚠️ Missing features in train data: {missing_features}")
    for feature in missing_features:
        train_df[feature] = np.nan  # Fill missing with NaN

if extra_features:
    print(f"⚠️ Extra features in train data (ignored): {extra_features}")
    train_df = train_df.drop(columns=list(extra_features), errors="ignore")

# Fill NaNs if any exist (shouldn't happen after preprocessing)
train_df.fillna(train_df.mean(), inplace=True)

# Convert to NumPy arrays
X_train, Y_train = train_df[feature_cols].values, train_df[target_cols].values

# Debug: Check for NaN in inputs
print("\n🔍 Checking for NaN values in target variables:")
print(train_df[target_cols].isna().sum())

print("\n🔍 Checking if target values are constant:")
print(train_df[target_cols].describe())

print("\n🔍 Checking for NaN values in input features:")
print(np.isnan(X_train).sum(), "NaN values found in X_train")

print("\n🔍 Checking if input features are constant:")
print(train_df[feature_cols].describe())

# If NaN values exist, stop training
if np.isnan(X_train).sum() > 0 or np.isnan(Y_train).sum() > 0:
    raise ValueError("❌ Training data contains NaN values. Check preprocessing!")

# Reshape for LSTM input (Samples, Time Steps, Features)
X_train = X_train.reshape((X_train.shape[0], 1, X_train.shape[1]))

# Debug: Check input shape before training
print("\n✅ Data successfully preprocessed!")
print("X_train shape:", X_train.shape, "Y_train shape:", Y_train.shape)

# **Define LSTM model**
model = keras.Sequential([
    layers.Input(shape=(X_train.shape[1], X_train.shape[2])),
    layers.LSTM(64, activation='relu', return_sequences=True),
    layers.Dropout(0.2),
    layers.LSTM(64, activation='relu'),
    layers.Dropout(0.2),
    layers.Dense(4)  # 4 output nodes for NO2 predictions (next 4 hours)
])

model.compile(optimizer='adam', loss='mse', metrics=['mae'])

# Train the model
history = model.fit(X_train, Y_train, epochs=50, batch_size=16, validation_split=0.2)

# Save the trained model
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

model.save(os.path.join(MODEL_DIR, "no2_forecast_model.keras"))  # Save in new format

print("\n✅ Training complete. Model saved.")