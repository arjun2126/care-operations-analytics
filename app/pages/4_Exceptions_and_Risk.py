import streamlit as st
from app.components import *
from src.analytics_metrics import calculate_exception_aging, calculate_rejection_rates, calculate_duplicate_risk, generate_narrative_observations
from src.risk_model import generate_risk_scores

def page():
    st.title("⚠️ Exceptions and Risk")
    st.markdown("**Decision supported: triage the highest-value and highest-risk claims and exceptions for analyst review.**")
    
    data, claims, funding, exceptions = load_all_data()
    
    st.markdown("### Exception KPIs")
    aging = calculate_exception_aging(exceptions)
    open_exceptions = aging[aging["exception_status"] != "Resolved"] if not aging.empty else pd.DataFrame()
    high_priority = open_exceptions[open_exceptions["priority"] == "High"] if not open_exceptions.empty else pd.DataFrame()
    open_exposure = float(open_exceptions["exception_amount"].sum()) if not open_exceptions.empty else 0.0
    
    kpi_card("Open Exceptions", f"{len(open_exceptions)}", "Unresolved", DANGER if len(open_exceptions) > 0 else SUCCESS)
    kpi_card("Exception Exposure", canadian_currency(open_exposure), "Open financial risk", DANGER)
    kpi_card("High-Priority Open", f"{len(high_priority)}", "Require immediate attention", DANGER if len(high_priority) > 0 else SUCCESS)
    
    risk_df = None
    if not claims.empty:
        risk_df = generate_risk_scores()
        if risk_df is not None and not risk_df.empty:
            high_risk = risk_df[risk_df["risk_band"] == "High"]
            kpi_card("High-Risk Claims", f"{len(high_risk)}", "Score ≥ 0.65", DANGER)
    
    st.markdown("### Exception Aging by Priority and Type")
    if not aging.empty:
        aging_display = aging[["exception_id", "claim_id", "exception_type", "priority", "exception_amount", "exception_status", "days_open"]].copy()
        aging_display.columns = ["Exception ID", "Claim ID", "Type", "Priority", "Amount", "Status", "Days Open"]
        aging_display["Amount"] = aging_display["Amount"].apply(canadian_currency)
        format_dataframe(aging_display.sort_values("Days Open", ascending=False))
    
    st.markdown("### Exception Exposure by Type")
    if not aging.empty and "exception_type" in aging.columns:
        exposure = aging.groupby("exception_type").agg(
            count=("exception_id", "count"),
            exposure=("exception_amount", "sum"),
        ).reset_index().sort_values("exposure", ascending=False)
        if not exposure.empty:
            fig = px.bar(exposure, x="exception_type", y="exposure", title="Exception Exposure by Type", color_discrete_sequence=[DANGER])
            fig.update_layout(yaxis_title="C$")
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### Claim Rejection Rates by Funder")
    rejection = calculate_rejection_rates(claims)
    if not rejection.empty:
        format_dataframe(rejection.sort_values("rejection_count", ascending=False))
    
    st.markdown("### Duplicate Claim Candidates")
    dup_risk = calculate_duplicate_risk(claims)
    if not dup_risk.empty:
        dup_risk["duplicate_exposure"] = dup_risk["duplicate_exposure"].apply(canadian_currency)
        format_dataframe(dup_risk.sort_values("duplicate_exposure", ascending=False))
        st.markdown(f"**{dup_risk['duplicate_count'].sum()} duplicate-candidate claims with {canadian_currency(dup_risk['duplicate_exposure'].sum())} in exposure.**")
    
    st.markdown("### Risk-Scored Claims Table")
    if risk_df is not None and not risk_df.empty:
        risk_display = risk_df[["claim_id", "client_id", "funder_id", "claim_amount", "risk_score", "risk_band", "reason_summary"]].copy()
        risk_display.columns = ["Claim ID", "Client ID", "Funder", "Claim Amount", "Risk Score", "Risk Band", "Reason Summary"]
        risk_display["Claim Amount"] = risk_display["Claim Amount"].apply(canadian_currency)
        risk_display["Risk Score"] = risk_display["Risk Score"].round(4)
        risk_display = risk_display.sort_values("Risk Score", ascending=False)
        
        band_colors = {"Low": SUCCESS, "Medium": WARNING, "High": DANGER}
        st.dataframe(risk_display.head(50), use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            low_count = len(risk_df[risk_df["risk_band"] == "Low"])
            st.metric("Low Risk Claims", f"{low_count}")
        with col2:
            med_count = len(risk_df[risk_df["risk_band"] == "Medium"])
            st.metric("Medium Risk Claims", f"{med_count}")
        with col3:
            high_count = len(risk_df[risk_df["risk_band"] == "High"])
            st.metric("High Risk Claims", f"{high_count}")
        
        band_dist = risk_df["risk_band"].value_counts().reset_index()
        band_dist.columns = ["Band", "Count"]
        fig = px.bar(band_dist, x="Band", y="Count", title="Risk Band Distribution", color="Band", color_discrete_map=band_colors)
        st.plotly_chart(fig, use_container_width=True)
    
    callout("Decision supported: triage the highest-value and highest-risk claims and exceptions for analyst review.", color=DANGER)
    synthetic_disclaimer()
    
    st.markdown("### ⚠️ Disclaimer")
    st.markdown("""
    **This is a synthetic-data prioritization aid. It does not automatically approve, deny, or determine care decisions.**
    The risk score is an interpretable analytics tool for triaging claims for analyst review, not an automated decision engine.
    """)

if __name__ == "__main__":
    page()