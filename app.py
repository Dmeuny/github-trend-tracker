import plotly.express as px
import streamlit as st
import psycopg2
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(
    page_title="GitHub Trend Tracker",
    page_icon="🚀",
    layout="wide"
)

# -----------------------
# HEADER
# -----------------------
st.title("🚀 GitHub Trend Tracker")
st.caption("Tracking momentum across Data Engineering and AI repos — updated daily via automated pipeline")
st.divider()


# -----------------------
# CONNECTION
# -----------------------

def get_connection():
    try:
        return psycopg2.connect(
            host=st.secrets["DB_HOST"],
            port=int(st.secrets["DB_PORT"]),
            database=st.secrets["DB_NAME"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            sslmode="require",
        )
    except Exception:
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 5432)),
            database=os.getenv("DB_NAME", "github"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD"),
        )


# -----------------------
# DATA LOAD
# -----------------------

# -----------------------
# DATA LOAD
# -----------------------

@st.cache_data(ttl=3600)
def load_trends():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT name, current_stars, prev_stars, star_growth, growth_pct, last_updated
        FROM dbt_dbt.repo_trends
    """, conn)
    conn.close()
    return df


@st.cache_data(ttl=3600)
def load_classification():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT name, topic_reclassified, de_score, ai_score
        FROM dbt_dbt.repo_classification
    """, conn)
    conn.close()
    return df


trends = load_trends()
classification = load_classification()


# -----------------------
# DATA PREP
# -----------------------

df = trends.merge(classification, on="name", how="left")


# -----------------------
# FILTERS
# -----------------------
category_filter = st.selectbox(
    "Filter by Category",
    options=["ALL", "DE", "AI", "OTHER"],
    index=0
)

filtered = df if category_filter == "ALL" else df[df["topic_reclassified"] == category_filter]


# -----------------------
# KPI METRICS
# -----------------------
st.subheader("Snapshot")
m1, m2, m3, m4 = st.columns(4)

m1.metric("Repos Tracked", len(filtered))
m2.metric("Total Stars", f"{filtered['current_stars'].sum():,.0f}")
m3.metric("Avg Growth %", f"{filtered['growth_pct'].mean():.2f}%")
m4.metric("Top Mover", filtered.iloc[0]["name"] if len(filtered) > 0 else "—")

st.divider()


# -----------------------
# TOP MOVERS CHART
# -----------------------
st.subheader("Top 10 by Growth %")

top10 = filtered.sort_values("growth_pct", ascending=False).head(10)

fig = px.bar(
    top10,
    x="growth_pct",
    y="name",
    orientation="h",
    color="growth_pct",
    color_continuous_scale=[
        "#e0f3ff",
        "#66b3ff",
        "#1f77b4"
    ],
)

fig.update_layout(
    yaxis=dict(categoryorder="total ascending")
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# -----------------------
# STAR GROWTH TABLE
# -----------------------
st.subheader("All Repos — Ranked by Growth")

display_df = filtered[[
    "name", "topic_reclassified", "current_stars", "star_growth", "growth_pct", "last_updated"
]].copy()

display_df.columns = ["Repo", "Category", "Stars", "Star Growth", "Growth %", "Last Updated"]

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Growth %": st.column_config.NumberColumn(format="%.2f%%"),
        "Stars": st.column_config.NumberColumn(format="%d"),
        "Star Growth": st.column_config.NumberColumn(format="+%d"),
    }
)

st.divider()


# -----------------------
# TOPIC BREAKDOWN
# -----------------------
st.subheader("Growth by Topic")

topic_summary = df.groupby("topic_reclassified").agg(
    repos=("name", "count"),
    avg_growth_pct=("growth_pct", "mean"),
    total_stars=("current_stars", "sum")
).reset_index()

st.dataframe(
    topic_summary,
    use_container_width=True,
    hide_index=True,
    column_config={
        "topic_reclassified": "Category",
        "repos": "Repos",
        "avg_growth_pct": st.column_config.NumberColumn("Avg Growth %", format="%.2f%%"),
        "total_stars": st.column_config.NumberColumn("Total Stars", format="%d"),
    }
)


# -----------------------
# FOOTER
# -----------------------
st.divider()
st.caption("Pipeline: GitHub API → Python (Prefect) → Postgres → dbt → Streamlit | Built by Dev Meunier")
