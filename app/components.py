import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys
import os

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.data_access import load_processed_data, get_data_source_status, load_claims_with_details, load_funding_with_claims, load_exceptions_with_claims, load_claims_risk_features
from src.analytics_metrics import calculate_executive_kpis, calculate_monthly_trends, calculate_worker_capacity, calculate_doc_delay_analysis, calculate_exception_aging, calculate_rejection_rates, calculate_duplicate_risk, generate_narrative_observations, calculate_funding_utilization, calculate_at_risk_funding

st.set_page_config(page_title="Care Operations Analytics", layout="wide", page_icon="🏥")

CADIAN_BLUE = "#1a3a5c"
ACCENT = "#2e86ab"
SUCCESS = "#27ae60"
WARNING = "#f39c12"
DANGER = "#e74c3c"
BACKGROUND = "#f8f9fa"

def canadian_currency(val: float) -> str:
    return f"C${val:,.2f}"

def canadian_pct(val: float) -> str:
    return f"{val:.1f}%"

def kpi_card(title: str, value: str, subtitle: str, color: str = ACCENT):
    st.markdown(
        f"""
        <div style="background: {BACKGROUND}; border-left: 4px solid {color}; padding: 12px 16px; border-radius: 4px; margin-bottom: 8px;">
            <div style="font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: 0.5px;">{title}</div>
            <div style="font-size: 24px; font-weight: 700; color: {color};">{value}</div>
            <div style="font-size: 12px; color: #888;">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def section_header(title: str, description: str):
    st.markdown(
        f"""
        <div style="border-bottom: 2px solid {ACCENT}; padding-bottom: 6px; margin-bottom: 12px;">
            <h2 style="color: {CADIAN_BLUE}; margin: 0;">{title}</h2>
            <p style="color: #666; font-size: 13px; margin: 4px 0 0 0;">{description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

def callout(message: str, color: str = WARNING):
    st.markdown(
        f"""
        <div style="background: #fff3cd; border-left: 4px solid {color}; padding: 10px 14px; border-radius: 4px; margin: 8px 0;">
            <p style="margin: 0; font-size: 13px;">{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

def synthetic_disclaimer():
    st.markdown(
        """
        <div style="background: #ffeaa7; border: 1px solid #fdcb6e; padding: 10px 14px; border-radius: 4px; margin: 12px 0;">
            <p style="margin: 0; font-size: 12px; color: #664a00;">
                <strong>⚠ Synthetic Portfolio Data:</strong> All data in this application is entirely synthetic and fictional. 
                No real personal, healthcare, client, employee, or company data is used.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

def load_all_data():
    data = load_processed_data()
    claims = load_claims_with_details()
    funding = load_funding_with_claims()
    exceptions = load_exceptions_with_claims()
    return data, claims, funding, exceptions

def get_sidebar_filters(claims: pd.DataFrame):
    st.sidebar.header("🔍 Filters")
    
    if "service_date" in claims.columns:
        claims["service_date"] = pd.to_datetime(claims["service_date"], errors="coerce")
        valid_dates = claims.dropna(subset=["service_date"])
        if not valid_dates.empty:
            date_range = st.sidebar.date_input(
                "Date Range",
                value=[valid_dates["service_date"].min(), valid_dates["service_date"].max()],
                min_value=valid_dates["service_date"].min(),
                max_value=valid_dates["service_date"].max(),
            )
            if len(date_range) == 2:
                claims = claims[
                    (claims["service_date"] >= pd.Timestamp(date_range[0])) &
                    (claims["service_date"] <= pd.Timestamp(date_range[1]))
                ]
    
    if "city" in claims.columns and claims["city"].notna().any():
        cities = sorted(claims["city"].dropna().unique())
        selected_cities = st.sidebar.multiselect("City", cities, default=cities[:5] if len(cities) > 5 else cities)
        if selected_cities:
            claims = claims[claims["city"].isin(selected_cities)]
    
    if "service_program" in claims.columns and claims["service_program"].notna().any():
        programs = sorted(claims["service_program"].dropna().unique())
        selected_programs = st.sidebar.multiselect("Service Program", programs, default=programs[:3] if len(programs) > 3 else programs)
        if selected_programs:
            claims = claims[claims["service_program"].isin(selected_programs)]
    
    if "funder_name" in claims.columns and claims["funder_name"].notna().any():
        funders = sorted(claims["funder_name"].dropna().unique())
        selected_funders = st.sidebar.multiselect("Funder", funders, default=funders[:3] if len(funders) > 3 else funders)
        if selected_funders:
            claims = claims[claims["funder_name"].isin(selected_funders)]
    
    return claims

def format_dataframe(df: pd.DataFrame, max_rows: int = 100):
    if df.empty:
        st.info("No data available for this view.")
        return
    display_df = df.head(max_rows).copy()
    for col in display_df.columns:
        if display_df[col].dtype == 'float64' or 'amount' in col.lower() or 'dollar' in col.lower():
            display_df[col] = display_df[col].apply(lambda x: canadian_currency(x) if isinstance(x, (int, float)) else x)
    st.dataframe(display_df, use_container_width=True)