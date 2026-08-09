import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

# ==============================
# Load Dataset
# ==============================

df = pd.read_csv("car_price_prediction.csv")

print("Dataset Loaded Successfully!")
print("Original Shape:", df.shape)

if "ID" in df.columns:
    df = df.drop(columns=["ID"])

# ==============================
# Data Cleaning & Feature Engineering
# ==============================

# 1. Clean Levy (الضريبة)
df["Levy"] = df["Levy"].astype(str).str.replace("-", "0")
df["Levy"] = pd.to_numeric(df["Levy"], errors="coerce").fillna(0)

df["Mileage"] = (
    df["Mileage"].astype(str).str.replace("km", "", regex=False).str.strip()
)
df["Mileage"] = pd.to_numeric(df["Mileage"], errors="coerce")

# 3. Clean Engine volume & Extract Turbo feature
df["Engine Turbo"] = df["Engine volume"].astype(str).str.contains("Turbo").astype(int)
df["Engine volume"] = (
    df["Engine volume"].astype(str).str.replace("Turbo", "", regex=False).str.strip()
)
df["Engine volume"] = pd.to_numeric(df["Engine volume"], errors="coerce")

doors_map = {"04-May": 4, "02-Mar": 2, ">5": 5}
df["Doors"] = df["Doors"].map(doors_map).fillna(4)

df["Car Age"] = 2026 - df["Prod. year"]
df = df.drop(columns=["Prod. year"])

df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
df = df[(df["Price"] >= 500) & (df["Price"] <= 100000)]
df = df[df["Mileage"] < 500000]

df = df.dropna()
print("Shape After Cleaning & Outlier Removal:", df.shape)

# ==============================
# Features and Target
# ==============================

X = df.drop("Price", axis=1)
y = np.log1p(df["Price"])

# ==============================
# Categorical Features
# ==============================

categorical_features = X.select_dtypes(include=["object"]).columns.tolist()

# ==============================
# Preprocessing Pipeline
# ==============================

preprocessor = ColumnTransformer(
    [
        (
            "categorical",
            OneHotEncoder(handle_unknown="ignore"),
            categorical_features,
        )
    ],
    remainder="passthrough",
)

# ==============================
# Model (Random Forest)
# ==============================

model = RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1)

# ==============================
# Pipeline Setup
# ==============================

pipeline = Pipeline([("preprocessing", preprocessor), ("model", model)])

# ==============================
# Split Dataset
# ==============================

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42
)

# ==============================
# Training
# ==============================

print("\nTraining Model...")
pipeline.fit(X_train, y_train)
print("Training Completed!")

# ==============================
# Predictions
# ==============================

log_predictions = pipeline.predict(X_test)

y_pred = np.expm1(log_predictions)
y_actual = np.expm1(y_test)

# ==============================
# Model Evaluation
# ==============================

mae = mean_absolute_error(y_actual, y_pred)
mse = mean_squared_error(y_actual, y_pred)
r2 = r2_score(y_actual, y_pred)

print("\n========== Model Evaluation ==========")
print(f"MAE      : {mae:.2f}")
print(f"MSE      : {mse:.2f}")
print(f"R2 Score : {r2:.2f}")

# ==============================
# Save Predictions
# ==============================

results = pd.DataFrame({"Actual Price": y_actual.values, "Predicted Price": y_pred})

results.to_csv("predictions.csv", index=False)

# ==============================
# Save Model
# ==============================

joblib.dump(pipeline, "car_price_model.pkl")

print("\nModel saved successfully!")
print("Files created:")
print("- predictions.csv")
print("- car_price_model.pkl")