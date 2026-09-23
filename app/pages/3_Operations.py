import streamlit as st
from app.components import *
from src.analytics_metrics import calculate_worker_capacity, calculate_doc_delay_analysis, calculate_monthly_trends

def page():
    st.title("⚙️ Operations")
    st.markdown("**Decision supported: Target staffing and documentation-process interventions before they affect claims and client service.**")
    
    data, claims, funding, exceptions = load_all_data()
    visits = data.get("service_visits", pd.DataFrame())
    workers = data.get("workers", pd.DataFrame())
    
    st.markdown("### Worker Capacity Utilization")
    capacity = calculate_worker_capacity(visits, workers)
    if not capacity.empty:
        st.markdown(f"**{len(capacity)} worker-weeks exceed weekly capacity.**")
        display = capacity[["worker_id", "worker_name", "worker_type", "weekly_capacity_hours", 
                            "week_start", "weekly_completed_hours", "capacity_utilization_pct"]].copy()
        display.columns = ["Worker ID", "Worker Name", "Type", "Capacity (hrs)", "Week Start", 
                           "Completed (hrs)", "Utilization %"]
        display["Utilization %"] = display["Utilization %"].round(1)
        format_dataframe(display.sort_values("Utilization %", ascending=False))
    else:
        st.info("No worker capacity violations detected in current data.")
    
    st.markdown("### Documentation Delay Trends")
    doc_delays = calculate_doc_delay_analysis(visits)
    if not doc_delays.empty:
        fig = px.bar(doc_delays, x="month", y="delay_count", title="Documentation Delays by Month", color_discrete_sequence=[WARNING])
        fig.update_layout(yaxis_title="Delayed Visits")
        st.plotly_chart(fig, use_container_width=True)
        
        if "avg_delay_days" in doc_delays.columns:
            avg_delay = doc_delays["avg_delay_days"].mean()
            st.metric("Average Documentation Delay (days)", f"{avg_delay:.1f}")
    
    if not visits.empty and "service_type" in visits.columns and "documentation_delay_days" in visits.columns:
        st.markdown("### Documentation Delays by Service Type")
        delay_by_service = visits[visits["documentation_delay_days"].notna() & (visits["documentation_delay_days"] > 0)].groupby("service_type").agg(
            delay_count=("visit_id", "count"),
            avg_delay=("documentation_delay_days", "mean"),
        ).reset_index().sort_values("delay_count", ascending=False)
        if not delay_by_service.empty:
            fig = px.bar(delay_by_service, x="service_type", y="delay_count", title="Delayed Visits by Service Type", color_discrete_sequence=[ACCENT])
            fig.update_layout(yaxis_title="Delayed Visits")
            st.plotly_chart(fig, use_container_width=True)
    
    if not visits.empty and "city" in visits.columns and "documentation_delay_days" in visits.columns:
        st.markdown("### Documentation Delays by City")
        delay_by_city = visits[visits["documentation_delay_days"].notna() & (visits["documentation_delay_days"] > 0)].groupby("city").agg(
            delay_count=("visit_id", "count"),
        ).reset_index().sort_values("delay_count", ascending=False).head(10)
        if not delay_by_city.empty:
            fig = px.bar(delay_by_city, x="city", y="delay_count", title="Top 10 Cities by Documentation Delays", color_discrete_sequence=[DANGER])
            fig.update_layout(yaxis_title="Delayed Visits")
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### Visit Status Breakdown")
    if not visits.empty and "visit_status" in visits.columns:
        status_counts = visits["visit_status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        fig = px.pie(status_counts, values="Count", names="Status", title="Visit Status Distribution", color_discrete_sequence=[SUCCESS, WARNING, DANGER])
        st.plotly_chart(fig, use_container_width=True)
    
    callout("Decision supported: target staffing and documentation-process interventions before they affect claims and client service.", color=ACCENT)
    synthetic_disclaimer()

if __name__ == "__main__":
    page()