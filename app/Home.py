import streamlit as st
from app.components import *

def page():
    st.title("🏥 Care Operations Analytics Command Center")
    st.markdown("**End-to-end analytics for Canadian care-services funding visibility, claims integrity, and operational efficiency.**")
    
    data, claims, funding, exceptions = load_all_data()
    
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        ### Business Problem
        A fictional Canadian care-services provider delivers in-home services funded by multiple funders. 
        Leaders lack visibility into:
        - **Funding utilization** and possible budget overruns
        - **Claims** likely to be rejected or need manual review
        - **Operational risks** such as late documentation and worker-capacity constraints
        - **Aging reconciliation exceptions** requiring resolution
        """)
    
    with col2:
        status = get_data_source_status()
        source_text = "✅ Loaded from validated processed CSV files." if status.get("all_loaded") else "⚠️ Some data files missing."
        st.info(source_text)
        synthetic_disclaimer()
    
    st.markdown("---")
    
    st.markdown("### Data Pipeline Architecture")
    st.markdown("""
    **Raw Synthetic Data → Data Quality Validation → Transformation/Cleaning → Processed CSV → Dashboard Analytics → Risk Scoring**
    
    - Generated via Faker with Canadian locale (300 clients, 110 workers, 6 funders, 7,500+ visits)
    - 53 data-quality checks applied; invalid records separated and logged
    - Processed data served as the primary source; optional PostgreSQL support available
    """)
    
    st.markdown("---")
    
    st.markdown("### Dashboard Pages")
    st.markdown("""
    | Page | Question Answered |
    |------|-------------------|
    | **1. Executive Overview** | Where is leadership attention needed first? |
    | **2. Funding Health** | Which allocations are approaching budget limits? |
    | **3. Operations** | Where are staffing and documentation bottlenecks? |
    | **4. Exceptions & Risk** | Which claims and exceptions should analysts review first? |
    """)
    
    st.markdown("---")
    
    st.markdown("### How to Run")
    st.code("""
# Generate data and run pipeline
python -m src.pipeline

# Generate risk scores
python -m src.risk_model

# Launch dashboard
streamlit run app/Home.py
    """, language="bash")
    
    st.markdown("---")
    
    st.markdown("### What This Demonstrates")
    st.markdown("""
    - **Python** — pandas, scikit-learn, Streamlit, Plotly
    - **SQL & Data Modelling** — Star schema with dimensions and facts
    - **Data Quality** — 53 reusable validation checks with audit trails
    - **Analytics** — Monthly trends, funding utilization, exception aging
    - **Dashboarding** — Interactive multi-page Streamlit app with Plotly
    - **Risk Prioritization** — Interpretable logistic regression claim scoring
    - **Consulting Recommendations** — Evidence-based findings from actual data
    """)
    
    synthetic_disclaimer()

if __name__ == "__main__":
    page()