import streamlit as st
import pandas as pd
from itertools import combinations

# -----------------------------
# CONFIG
# -----------------------------
DIMENSIONS = [
    "brand",
    "indication",
    "vendor",
    "month",
    "vehicle"
]

st.set_page_config(
    page_title="Metric Cube Explorer",
    layout="wide"
)

st.title("📊 Metric Cube Explorer")

# -----------------------------
# LOAD DATA (CACHED)
# -----------------------------
@st.cache_data
def load_data():
    return pd.read_csv("hcp_marketing_metrics_100k.csv")

df_lung = load_data()

# -----------------------------
# METRIC LOGIC
# -----------------------------
def calculate_metrics(df, group_by_cols):
    reach_df = df[df["metric_category"] == "REACH"]
    engagement_df = df[df["metric_category"] == "ENGAGEMENT"]

    reached = (
        reach_df
        .groupby(group_by_cols, dropna=False)
        .agg(
            HCP_REACHED=("bp_id", "nunique"),
            REACHED_TPS=("value", "sum")
        )
        .reset_index()
    )

    engaged = (
        engagement_df
        .groupby(group_by_cols, dropna=False)
        .agg(
            HCPS_ENGAGED=("bp_id", "nunique"),
            ENGAGED_TPS=("value", "sum")
        )
        .reset_index()
    )

    final = reached.merge(engaged, on=group_by_cols, how="left")
    final[["HCPS_ENGAGED", "ENGAGED_TPS"]] = final[
        ["HCPS_ENGAGED", "ENGAGED_TPS"]
    ].fillna(0)

    return final

# -----------------------------
# BUILD METRIC CUBE (CACHED)
# -----------------------------
@st.cache_data
def build_metric_cube(df):
    cubes = {}

    for i in range(1, len(DIMENSIONS) + 1):
        for combo in combinations(DIMENSIONS, i):
            key = tuple(sorted(combo))
            cubes[key] = calculate_metrics(df, list(combo))

    return cubes

metric_cube = build_metric_cube(df_lung)

# -----------------------------
# UI
# -----------------------------
selected_dims = st.multiselect(
    "Choose dimensions",
    DIMENSIONS
)

if selected_dims:
    key = tuple(sorted(selected_dims))
    result = metric_cube.get(key)

    if result is None or result.empty:
        st.warning("Granularity not supported or no data.")
    else:
        st.success(f"Showing summary for: {', '.join(key)}")
        st.dataframe(result, use_container_width=True)

        # Download
        st.download_button(
            "⬇️ Download CSV",
            result.to_csv(index=False),
            file_name=f"metrics_{'_'.join(key)}.csv",
            mime="text/csv"
        )
else:
    st.info("Select at least one dimension")
