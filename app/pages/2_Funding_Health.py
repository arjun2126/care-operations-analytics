import streamlit as st
from app.components import *
from src.analytics_metrics import calculate_funding_utilization, calculate_at_risk_funding, calculate_executive_kpis, generate_narrative_observations

def page():
    st.title("💰 Funding Health")
    st.markdown("**Decision supported: Prioritize proactive funding review and prevent service disruption or unapproved spend.**")
    
    data, claims, funding, exceptions = load_all_data()
    visits = data.get("service_visits", pd.DataFrame())
    
    funding_util = calculate_funding_utilization(funding)
    at_risk = calculate_at_risk_funding(funding)
    
    st.markdown("### Allocation vs Approved Spend by Funder")
    if not funding_util.empty:
        if "funder_name" in funding_util.columns:
            group_col = "funder_name"
        elif "funder_id" in funding_util.columns:
            group_col = "funder_id"
        else:
            group_col = None
        
        if group_col:
            funder_summary = funding_util.groupby(group_col).agg(
                allocated=("allocated_amount", "sum"),
                approved_spend=("total_approved_spend", "sum"),
            ).reset_index()
            funder_summary["remaining"] = funder_summary["allocated"] - funder_summary["approved_spend"]
            funder_summary["utilization_pct"] = (funder_summary["approved_spend"] / funder_summary["allocated"].replace(0, pd.NA) * 100).fillna(0).round(1)
            
            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(funder_summary, x=group_col, y="allocated", title="Allocated vs Approved Spend", color_discrete_sequence=[ACCENT])
                fig.update_layout(yaxis_title="C$")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = px.bar(funder_summary, x=group_col, y="utilization_pct", title="Funding Utilization by Funder (%)", color_discrete_sequence=[WARNING])
                fig.update_layout(yaxis_title="%")
                st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### Client-Funder Allocation Table")
    if not funding_util.empty:
        display_cols = ["allocation_id", "client_id", "funder_id", "allocated_amount", "total_approved_spend", "remaining_funding", "utilization_pct"]
        available_cols = [c for c in display_cols if c in funding_util.columns]
        if "at_risk" in funding_util.columns:
            available_cols.append("at_risk")
        
        display_df = funding_util[available_cols].copy()
        display_df.columns = [c.replace("_", " ").title() for c in available_cols]
        for col in display_df.columns:
            if "amount" in col.lower() or "spend" in col.lower() or "remaining" in col.lower() or "allocated" in col.lower():
                display_df[col] = display_df[col].apply(lambda x: canadian_currency(x) if isinstance(x, (int, float)) else x)
        display_df = display_df.sort_values("Utilization Pct" if "Utilization Pct" in display_df.columns else display_df.columns[-1], ascending=False)
        format_dataframe(display_df)
    
    if not at_risk.empty:
        st.markdown("### 🚨 Allocations At Risk (≥90% Utilization)")
        risk_cols = ["allocation_id", "client_id", "funder_id", "allocated_amount", "total_approved_spend", "remaining_funding", "utilization_pct"]
        available_risk_cols = [c for c in risk_cols if c in at_risk.columns]
        risk_display = at_risk[available_risk_cols].copy()
        for col in risk_display.columns:
            if "amount" in col.lower() or "spend" in col.lower() or "remaining" in col.lower() or "allocated" in col.lower():
                risk_display[col] = risk_display[col].apply(lambda x: canadian_currency(x) if isinstance(x, (int, float)) else x)
        format_dataframe(risk_display.sort_values("Utilization Pct" if "Utilization Pct" in risk_display.columns else risk_display.columns[-1], ascending=False))
        st.markdown(f"**{len(at_risk)} allocations are at or above 90% utilization.**")
    
    kpis = calculate_executive_kpis(claims, visits, exceptions, funding)
    observations = generate_narrative_observations(kpis, pd.DataFrame(), funding, exceptions)
    st.markdown("### Narrative")
    for obs in observations[:3]:
        st.markdown(f"- {obs}")
    
    callout("Decision supported: prioritize proactive funding review and prevent service disruption or unapproved spend.", color=WARNING)
    synthetic_disclaimer()

if __name__ == "__main__":
    page()