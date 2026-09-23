import streamlit as st
from app.components import *
from src.analytics_metrics import calculate_executive_kpis, calculate_monthly_trends, generate_narrative_observations, calculate_at_risk_funding

def page():
    st.title("📊 Executive Overview")
    st.markdown("**Decision supported: Identify where leadership attention is needed first.**")
    
    data, claims, funding, exceptions = load_all_data()
    claims = get_sidebar_filters(claims)
    
    visits = data.get("service_visits", pd.DataFrame())
    if not claims.empty and not visits.empty:
        claims_visits = claims.merge(visits, on="visit_id", how="left")
    else:
        claims_visits = claims
    
    kpis = calculate_executive_kpis(claims_visits, visits, exceptions, funding)
    
    st.markdown("### Key Performance Indicators")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    kpi_card("Total Visits", f"{kpis['total_visits']:,}", "All statuses", ACCENT)
    kpi_card("Completed Hours", f"{kpis['completed_hours']:,.1f}", "Total billed hours", SUCCESS)
    kpi_card("Claim Dollars", canadian_currency(kpis['total_claim_dollars']), "Total claimed", ACCENT)
    kpi_card("Approval Rate", canadian_pct(kpis['approval_rate']), "Approved / total", SUCCESS if kpis['approval_rate'] >= 60 else WARNING)
    kpi_card("Open Exceptions", f"{kpis['open_exceptions']}", "Unresolved items", DANGER if kpis['open_exceptions'] > 0 else SUCCESS)
    kpi_card("Funding At Risk", f"{kpis['funding_at_risk_count']}", "≥90% utilization", DANGER if kpis['funding_at_risk_count'] > 0 else SUCCESS)
    
    st.markdown("### Monthly Trends")
    monthly = calculate_monthly_trends(visits, claims, exceptions)
    
    if not monthly.empty:
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(monthly, x="month_label", y="total_visits", title="Monthly Service Volume", color_discrete_sequence=[ACCENT])
            fig.update_layout(yaxis_title="Visits")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.line(monthly, x="month_label", y="completed_hours", title="Monthly Completed Hours", color_discrete_sequence=[SUCCESS])
            fig.update_layout(yaxis_title="Hours")
            st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(monthly, x="month_label", y="claim_dollars", title="Monthly Claim Dollars", color_discrete_sequence=[ACCENT])
            fig.update_layout(yaxis_title="C$")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.line(monthly, x="month_label", y="approval_rate", title="Monthly Approval Rate (%)", color_discrete_sequence=[WARNING])
            fig.update_layout(yaxis_title="%")
            st.plotly_chart(fig, use_container_width=True)
        
        fig = px.bar(monthly, x="month_label", y="exception_count", title="Monthly Exception Count", color_discrete_sequence=[DANGER])
        fig.update_layout(yaxis_title="Exceptions")
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### Key Observations")
    observations = generate_narrative_observations(kpis, monthly, calculate_at_risk_funding(funding), calculate_exception_aging(exceptions))
    for obs in observations:
        st.markdown(f"- {obs}")
    
    callout("Decision supported: identify where leadership attention is needed first.", color=ACCENT)
    synthetic_disclaimer()

if __name__ == "__main__":
    page()