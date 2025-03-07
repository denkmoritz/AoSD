import pandas as pd
from sklearn.preprocessing import RobustScaler
import os
import joblib

# Paths
DATA_DIR = "data/"
OUTPUT_DIR = "data/"

# Load data
train_df = pd.read_csv(os.path.join(DATA_DIR, "new_data_for_model.csv"))
eval_df = pd.read_csv(os.path.join(DATA_DIR, "evaluation_data_for_model.csv"))

# Rename NO2 measurement column
train_df.rename(columns={"measurement_value": "NO2_t"}, inplace=True)
eval_df.rename(columns={"measurement_value": "NO2_t"}, inplace=True)

# Define feature columns
past_no2_cols = [f'NO2_lag_{i}' for i in range(1, 5)]
past_weather_cols = [f'past_wind_{i}' for i in range(1, 5)] + \
                    [f'past_wind_dir_{i}' for i in range(1, 5)] + \
                    [f'past_pressure_{i}' for i in range(1, 5)] + \
                    [f'past_humidity_{i}' for i in range(1, 5)] + \
                    [f'past_temp_{i}' for i in range(1, 5)]

future_weather_cols = [f'future_wind_{i}' for i in range(1, 5)] + \
                      [f'future_wind_dir_{i}' for i in range(1, 5)] + \
                      [f'future_pressure_{i}' for i in range(1, 5)] + \
                      [f'future_humidity_{i}' for i in range(1, 5)] + \
                      [f'future_temp_{i}' for i in range(1, 5)]

# Create future NO2 target columns in train data
for i in range(1, 5):
    train_df[f'NO2_target_T+{i}'] = train_df['NO2_t'].shift(-i)

# Define input features
input_features = ["NO2_t"] + past_no2_cols + past_weather_cols + future_weather_cols
target_columns = [f'NO2_target_T+{i}' for i in range(1, 5)]  # Future NO₂ values

# Training dataset includes target columns, but they should NOT be scaled
train_features = input_features + target_columns
eval_features = input_features + target_columns  # Evaluation dataset must include targets for comparison

# Ensure train & eval datasets have the same feature structure
train_processed = train_df.reindex(columns=train_features)
eval_processed = eval_df.reindex(columns=eval_features)

# Drop rows where `NO2_t` or targets are NaN (evaluation doesn't have future NO₂)
train_processed.dropna(subset=["NO2_t"] + target_columns, inplace=True)
eval_processed.dropna(subset=["NO2_t"] + past_no2_cols, inplace=True)

# Fill missing values with column mean
train_processed.fillna(train_processed.mean(), inplace=True)
eval_processed.fillna(eval_processed.mean(), inplace=True)

# ✅ **Use RobustScaler**
scaler = RobustScaler()
scaler.fit(train_processed[input_features])  # Fit scaler only on training input features

# ✅ Apply Scaling Properly
train_scaled = train_processed.copy()
eval_scaled = eval_processed.copy()

# Scale only input features (leave targets unscaled)
train_scaled[input_features] = scaler.transform(train_processed[input_features])
eval_scaled[input_features] = scaler.transform(eval_processed[input_features])

# ✅ **Debug Scaling**
print("\n✅ Checking Scaling - Train Data:")
print(train_scaled[input_features].describe())

print("\n✅ Checking Scaling - Eval Data:")
print(eval_scaled[input_features].describe())

# ✅ **Check if Scaling is Out of Bounds**
if train_scaled[input_features].min().min() < -3 or train_scaled[input_features].max().max() > 3:
    print("🚨 WARNING: Training data contains out-of-range values. Fixing...")
    train_scaled[input_features] = train_scaled[input_features].clip(-3, 3)

if eval_scaled[input_features].min().min() < -3 or eval_scaled[input_features].max().max() > 3:
    print("🚨 WARNING: Evaluation data contains out-of-range values. Fixing...")
    eval_scaled[input_features] = eval_scaled[input_features].clip(-3, 3)

# Save processed data
train_scaled.to_csv(os.path.join(OUTPUT_DIR, "train_preprocessed.csv"), index=False)
eval_scaled.to_csv(os.path.join(OUTPUT_DIR, "eval_preprocessed.csv"), index=False)
joblib.dump(scaler, os.path.join(OUTPUT_DIR, "scaler.pkl"))

# ✅ **Print Min and Max Values of Scaled Data**
print("\n✅ Scaled Data Min and Max Values:")
print("Train Scaled Min:\n", train_scaled[input_features].min())
print("Train Scaled Max:\n", train_scaled[input_features].max())
print("Eval Scaled Min:\n", eval_scaled[input_features].min())
print("Eval Scaled Max:\n", eval_scaled[input_features].max())

print("\n✅ Preprocessing complete. Processed files saved.")