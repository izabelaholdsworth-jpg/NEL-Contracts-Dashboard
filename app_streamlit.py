import pandas as pd
import streamlit as st

# ---------- CONFIG ----------
st.set_page_config(page_title="NEL Contract & Provider Explorer", layout="wide")

# ---------- LOAD DATA ----------
@st.cache_data
def load_data():
    path = r"C:\Users\izabe\OneDrive\Desktop\NEL_Contract_Data\NEL_Main_Enriched_Output.xlsx"
    df = pd.read_excel(path, sheet_name="merged_data")
    return df

df = load_data()

st.title("💼 NEL Contract & Provider Explorer")

# ---------- FILTER SIDEBAR ----------
st.sidebar.header("Filters")

org_types = sorted(df["OrgType"].dropna().unique())
category = sorted(df["Category"].dropna().unique())

if "enr_CQC_Rating" in df.columns:
    cqc_ratings = sorted(df["enr_CQC_Rating"].dropna().unique())
else:
    cqc_ratings = []

selected_orgtype = st.sidebar.multiselect("Organisation Type", org_types, default=org_types)
selected_category = st.sidebar.multiselect("Category", category, default=category)
selected_rating = st.sidebar.multiselect("CQC Rating", cqc_ratings, default=cqc_ratings)

# Contract Value range
df["Contract Value"] = pd.to_numeric(df["Contract Value"], errors="coerce")
min_val = float(df["Contract Value"].min())
max_val = float(df["Contract Value"].max())

contract_value_range = st.sidebar.slider(
    "Contract Value (£)", 
    min_val, 
    max_val, 
    (min_val, max_val)
)

# ---------- APPLY FILTERS ----------
filtered_df = df[
    df["OrgType"].isin(selected_orgtype)
    & df["Category"].isin(selected_category)
    & df["Contract Value"].between(*contract_value_range)
]

if cqc_ratings:
    filtered_df = filtered_df[filtered_df["enr_CQC_Rating"].isin(selected_rating)]

# ---------- AGGREGATE BY PROVIDER ----------
agg_df = (
    filtered_df.groupby(
        ["Provider", "OrgType", "Category", "enr_CQC_Rating", "enr_Summary", "enr_Companies_House_Info"],
        dropna=False,
        as_index=False
    )["Contract Value"].sum()
)

agg_df = agg_df.sort_values(by="Contract Value", ascending=False)

st.markdown(f"**{len(agg_df):,} unique providers shown** after aggregation")

# ---------- TABLE VIEW ----------
st.dataframe(
    agg_df[
        [
            "Provider",
            "Contract Value",
            "OrgType",
            "Category",
            "enr_CQC_Rating",
            "enr_Summary",
            "enr_Companies_House_Info",
        ]
    ],
    width="stretch",
    hide_index=True,
)

# ---------- DOWNLOAD BUTTON ----------
csv = agg_df.to_csv(index=False).encode("utf-8")
st.download_button("📥 Download filtered aggregated data (CSV)", csv, "NEL_filtered_aggregated.csv", "text/csv")

# ---------- PRIVATE PROVIDERS £1m–£4m RANGE ----------
st.markdown("## 🏢 Private Providers (£1m–£4m Contract Value Range)")

private_df = df[
    (df["OrgType"] == "Independent Ltd/LLP/Co.")
    & (df["Category"] == "Private Community Sector Providers (Non NHS)")
].copy()

private_df["Contract Value"] = pd.to_numeric(private_df["Contract Value"], errors="coerce")

# Aggregate spend per provider
private_agg = (
    private_df.groupby("Provider", as_index=False)["Contract Value"]
    .sum()
)

# Filter for £1m–£4m providers (DESCENDING order)
filtered_private = private_agg[
    (private_agg["Contract Value"] >= 1_000_000)
    & (private_agg["Contract Value"] <= 4_000_000)
].sort_values(by="Contract Value", ascending=False)

# Display table
st.dataframe(filtered_private, width="stretch", hide_index=True)

import altair as alt

# ---------- DESCENDING BAR CHART (sorted by Contract Value) ----------
chart = (
    alt.Chart(filtered_private)
    .mark_bar(color="#1f77b4")
    .encode(
        x=alt.X(
            "Provider:N",
            sort="-y",
            title="Provider",
            axis=alt.Axis(labelAngle=-45)
        ),
        y=alt.Y(
            "Contract Value:Q",
            title="Contract Value (£)"
        ),
        tooltip=[
            alt.Tooltip("Provider:N", title="Provider"),
            alt.Tooltip("Contract Value:Q", format=",.0f", title="Value (£)")
        ]
    )
    .properties(height=400)
)

st.altair_chart(chart, use_container_width=True)



# ---------- FOOTER ----------
st.markdown("---")
st.caption("Data source: NEL Contract Data (enriched via Python merge pipeline).")
