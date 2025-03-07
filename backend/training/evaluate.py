import pandas as pd
import numpy as np
import joblib
import os
import keras
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Paths
DATA_DIR = "data/"
MODEL_DIR = "models/"

# Load evaluation data
eval_df = pd.read_csv(os.path.join(DATA_DIR, "eval_preprocessed.csv"))

# Load trained model
model = keras.models.load_model(os.path.join(MODEL_DIR, "no2_forecast_model.keras"))

# Define expected input features
target_cols = [f'NO2_target_T+{i}' for i in range(1, 5)]
expected_features = [col for col in eval_df.columns if col not in target_cols]  # Input features only

# **Step 1: Ensure Evaluation Data Has the Correct Features**
missing_features = set(expected_features) - set(eval_df.columns)
extra_features = set(eval_df.columns) - set(expected_features) - set(target_cols)

if missing_features:
    raise ValueError(f"🚨 ERROR: Missing features in eval data: {missing_features}")

if extra_features:
    print(f"⚠️ Warning: Extra features in eval data (will be ignored): {extra_features}")
    eval_df = eval_df.drop(columns=list(extra_features))

# **Step 2: Extract Input Features**
X_eval_scaled = eval_df[expected_features].values  # Use preprocessed features directly

# **Step 3: Debug Input Data Check**
print("\n🔍 Debug Input Data Check:")
print("📉 X_eval_scaled min:", X_eval_scaled.min())
print("📈 X_eval_scaled max:", X_eval_scaled.max())

# **Step 4: Reshape for LSTM Input**
X_eval_scaled = X_eval_scaled.reshape((X_eval_scaled.shape[0], 1, X_eval_scaled.shape[1]))

# Predict on evaluation set
Y_pred = model.predict(X_eval_scaled)

# **Step 5: Debug Predictions Check**
print("\n🔍 Debug Predictions Check:")
print("📉 Y_pred min:", Y_pred.min())
print("📈 Y_pred max:", Y_pred.max())

# If negative values persist, apply clipping
Y_pred = np.maximum(Y_pred, 0)  # Ensure NO2 values can't be negative

# Convert to DataFrame
predictions_df = pd.DataFrame({
    "Actual_NO2_t+1": eval_df[target_cols[0]],
    "Predicted_NO2_t+1": Y_pred[:, 0],
    "Actual_NO2_t+2": eval_df[target_cols[1]],
    "Predicted_NO2_t+2": Y_pred[:, 1],
    "Actual_NO2_t+3": eval_df[target_cols[2]],
    "Predicted_NO2_t+3": Y_pred[:, 2],
    "Actual_NO2_t+4": eval_df[target_cols[3]],
    "Predicted_NO2_t+4": Y_pred[:, 3],
})

# Show first 20 predictions
print(predictions_df.head(20))

# Compute metrics
mae = mean_absolute_error(eval_df[target_cols], Y_pred)
rmse = np.sqrt(mean_squared_error(eval_df[target_cols], Y_pred))

print(f"📊 MAE: {mae:.3f}, RMSE: {rmse:.3f}")

# Plot results
plt.figure(figsize=(12, 8))
for i in range(4):
    plt.subplot(2, 2, i + 1)
    plt.plot(eval_df[target_cols[i]], label=f"Actual NO2 t+{i+1}", linestyle="dashed")
    plt.plot(Y_pred[:, i], label=f"Predicted NO2 t+{i+1}")
    plt.legend()
    plt.xlabel("Time")
    plt.ylabel("NO2")
    plt.title(f"{i+1}-Hour Ahead NO2 Prediction")

plt.tight_layout()
plt.show()