import joblib
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Car Price Prediction", page_icon="🚗", layout="wide"
)


# ==================================================
# LOAD & PREPROCESS DATA
# ==================================================


@st.cache_data
def load_data():
    df = pd.read_csv("car_price_prediction.csv")

    if "ID" in df.columns:
        df = df.drop(columns=["ID"])

    df["Levy"] = df["Levy"].astype(str).str.replace("-", "0")
    df["Levy"] = pd.to_numeric(df["Levy"], errors="coerce").fillna(0)

    df["Mileage"] = (
        df["Mileage"].astype(str).str.replace("km", "", regex=False).str.strip()
    )
    df["Mileage"] = pd.to_numeric(df["Mileage"], errors="coerce")

    df["Engine Turbo"] = (
        df["Engine volume"].astype(str).str.contains("Turbo").astype(int)
    )
    df["Engine volume"] = (
        df["Engine volume"]
        .astype(str)
        .str.replace("Turbo", "", regex=False)
        .str.strip()
    )
    df["Engine volume"] = pd.to_numeric(df["Engine volume"], errors="coerce")

    doors_map = {"04-May": 4, "02-Mar": 2, ">5": 5}
    df["Doors"] = df["Doors"].map(doors_map).fillna(4)

    df["Car Age"] = 2026 - df["Prod. year"]

    df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
    df = df[(df["Price"] >= 500) & (df["Price"] <= 100000)]
    df = df[df["Mileage"] < 500000]

    return df.dropna()


df = load_data()

try:
    model = joblib.load("car_price_model.pkl")
    results = pd.read_csv("predictions.csv")
except Exception as e:
    st.error("⚠️ Please run the model training code first to generate the model and prediction files.")
    st.stop()


# ==================================================
# HEADER
# ==================================================

st.title("🚗 Car Price Prediction")
st.markdown("### AI-Powered Car Price Estimation")
st.write(
    "Predict the expected price of a car using Machine Learning based on its specifications and condition."
)

st.divider()


# ==================================================
# STATISTICS
# ==================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🚘 Total Cars", f"{len(df):,}")

with col2:
    st.metric("💰 Average Price", f"${df['Price'].mean():,.0f}")

with col3:
    st.metric("📈 Maximum Price", f"${df['Price'].max():,.0f}")

with col4:
    st.metric("📉 Minimum Price", f"${df['Price'].min():,.0f}")

st.divider()


# ==================================================
# PRICE DISTRIBUTION
# ==================================================

st.subheader("📊 Distribution of Cars Prices")

fig_distribution = px.histogram(
    df,
    x="Price",
    nbins=35,
    title="Distribution of Cars Prices",
    labels={"Price": "Car Price ($)", "count": "Number of Cars"},
    marginal="box",
)

fig_distribution.update_traces(
    hovertemplate="Price: $%{x:,.0f}<br>Cars: %{y}<extra></extra>"
)

fig_distribution.update_layout(
    height=500,
    template="plotly_white",
    title_x=0.5,
    bargap=0.08,
    xaxis=dict(showgrid=False, tickformat="$,.0f"),
    yaxis=dict(showgrid=True, gridcolor="lightgray"),
)

st.plotly_chart(fig_distribution, use_container_width=True)

st.divider()


# ==================================================
# ACTUAL VS PREDICTED
# ==================================================

st.subheader("🎯 Actual Price vs Predicted Price")

fig_prediction = go.Figure()

fig_prediction.add_trace(
    go.Scatter(
        x=results["Actual Price"],
        y=results["Predicted Price"],
        mode="markers",
        name="Predictions",
        text=[
            f"Actual: ${a:,.0f}<br>Predicted: ${p:,.0f}"
            for a, p in zip(results["Actual Price"], results["Predicted Price"])
        ],
        hoverinfo="text",
    )
)

min_price = min(
    results["Actual Price"].min(), results["Predicted Price"].min()
)
max_price = max(
    results["Actual Price"].max(), results["Predicted Price"].max()
)

fig_prediction.add_trace(
    go.Scatter(
        x=[min_price, max_price],
        y=[min_price, max_price],
        mode="lines",
        name="Perfect Prediction",
        line=dict(dash="dash", color="red"),
    )
)

fig_prediction.update_layout(
    height=500,
    template="plotly_white",
    title_x=0.5,
    xaxis_title="Actual Price ($)",
    yaxis_title="Predicted Price ($)",
    legend_title="Legend",
)

st.plotly_chart(fig_prediction, use_container_width=True)

st.divider()


# ==================================================
# PRICE COMPARISON
# ==================================================

st.subheader("📈 Actual vs Predicted Price (Sample)")

comparison = results.head(20).reset_index()

fig_comparison = go.Figure()

fig_comparison.add_trace(
    go.Bar(
        x=comparison.index + 1,
        y=comparison["Actual Price"],
        name="Actual Price",
    )
)

fig_comparison.add_trace(
    go.Bar(
        x=comparison.index + 1,
        y=comparison["Predicted Price"],
        name="Predicted Price",
    )
)

fig_comparison.update_layout(
    height=450,
    template="plotly_white",
    barmode="group",
    xaxis_title="Car Sample",
    yaxis_title="Price ($)",
    title="Actual and Predicted Prices Sample",
)

st.plotly_chart(fig_comparison, use_container_width=True)

st.divider()


# ==================================================
# CAR PRICE PREDICTION
# ==================================================

st.subheader("🔮 Predict a Car Price")

col_a, col_b, col_c = st.columns(3)

with col_a:
    manufacturer = st.selectbox(
        "🏭 Manufacturer", sorted(df["Manufacturer"].unique())
    )

    available_models = df[df["Manufacturer"] == manufacturer]["Model"].unique()
    model_name = st.selectbox("🚘 Model", sorted(available_models))

    category = st.selectbox("🚙 Category", sorted(df["Category"].unique()))

    prod_year = st.number_input(
        "📅 Production Year",
        min_value=int(df["Prod. year"].min()),
        max_value=int(df["Prod. year"].max()),
        value=2015,
    )

    color = st.selectbox("🎨 Color", sorted(df["Color"].unique()))

with col_b:
    fuel_type = st.selectbox("⛽ Fuel Type", sorted(df["Fuel type"].unique()))

    gear_box = st.selectbox(
        "⚙️ Gear Box Type", sorted(df["Gear box type"].unique())
    )

    drive_wheels = st.selectbox(
        "🏎️ Drive Wheels", sorted(df["Drive wheels"].unique())
    )

    wheel = st.selectbox("🎡 Wheel Position", sorted(df["Wheel"].unique()))

    leather = st.radio("🛋️ Leather Interior", ["Yes", "No"], horizontal=True)

with col_c:
    engine_vol = st.number_input(
        "⚙️ Engine Volume",
        min_value=0.5,
        max_value=10.0,
        value=float(df["Engine volume"].mean()),
        step=0.1,
    )

    is_turbo = st.checkbox("🚀 Turbo Engine")

    mileage_val = st.number_input(
        "🛣️ Mileage (km)",
        min_value=0,
        max_value=500000,
        value=int(df["Mileage"].median()),
        step=1000,
    )

    cylinders = st.number_input(
        "🔲 Cylinders", min_value=1.0, max_value=16.0, value=4.0, step=1.0
    )

    airbags = st.slider("🎈 Airbags", min_value=0, max_value=16, value=4)

    doors = st.selectbox("🚪 Doors", [2, 4, 5], index=1)

    levy_val = st.number_input(
        "💵 Levy ($)", min_value=0, value=int(df["Levy"].median())
    )


# ==================================================
# PREDICTION BUTTON
# ==================================================

st.write("")

if st.button("🚀 Predict Car Price", use_container_width=True):

    input_data = pd.DataFrame(
        {
            "Levy": [levy_val],
            "Manufacturer": [manufacturer],
            "Model": [model_name],
            "Category": [category],
            "Leather interior": [leather],
            "Fuel type": [fuel_type],
            "Engine volume": [engine_vol],
            "Mileage": [mileage_val],
            "Cylinders": [cylinders],
            "Gear box type": [gear_box],
            "Drive wheels": [drive_wheels],
            "Doors": [doors],
            "Wheel": [wheel],
            "Color": [color],
            "Airbags": [airbags],
            "Engine Turbo": [1 if is_turbo else 0],
            "Car Age": [2026 - prod_year],
        }
    )

    log_pred = model.predict(input_data)[0]
    predicted_price = np.expm1(log_pred)

    st.success(f"💰 Estimated Car Price: **${predicted_price:,.2f}**")

    st.info(
        "The price above was estimated using the trained Machine Learning Model."
    )


# ==================================================
# FOOTER
# ==================================================

st.divider()

st.caption("Car Price Prediction System | Machine Learning Project")