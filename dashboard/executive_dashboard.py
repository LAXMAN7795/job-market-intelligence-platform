import streamlit as st
import plotly.express as px
import pandas as pd
from sqlalchemy import func
from database.postgres import db_session, Job, Company, Skill
from analytics.salary_analysis import get_average_salary
from analytics.hiring_analysis import get_top_locations, get_top_industries, get_top_roles
from analytics.skill_analysis import get_top_skills


def render_kpi_card(title: str, value: str, icon: str, description: str = ""):
    """Renders a beautifully styled HTML/CSS KPI card."""
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-card-header">
                <span class="kpi-card-icon">{icon}</span>
                <span class="kpi-card-title">{title}</span>
            </div>
            <div class="kpi-card-value">{value}</div>
            {f'<div class="kpi-card-desc">{description}</div>' if description else ''}
        </div>
        """,
        unsafe_allow_html=True
    )


def show_executive_dashboard():
    """Renders the executive summary dashboard page."""
    st.markdown("<h2 class='page-title'>Executive Summary</h2>", unsafe_allow_html=True)
    st.markdown("<p class='page-subtitle'>High-level insights and key performance indicators from across the job market.</p>", unsafe_allow_html=True)

    # 1. Fetch KPI metrics
    session = db_session()
    try:
        total_jobs = session.query(func.count(Job.job_id)).scalar() or 0
        total_companies = session.query(func.count(Company.company_id)).scalar() or 0
        total_skills = session.query(func.count(Skill.skill_id)).scalar() or 0
    finally:
        session.close()
        
    avg_salary = get_average_salary()
    avg_sal_str = f"{avg_salary} LPA" if avg_salary > 0 else "N/A"
    
    loc_df = get_top_locations(limit=1)
    top_city = loc_df.iloc[0]["Location"] if not loc_df.empty else "N/A"
    
    skill_df = get_top_skills(limit=1)
    top_skill = skill_df.iloc[0]["Skill"] if not skill_df.empty else "N/A"
    
    # 2. Render KPIs in 3 columns, 2 rows
    col1, col2, col3 = st.columns(3)
    with col1:
        render_kpi_card("Total Job Listings", f"{total_jobs:,}", "💼", "Aggregated vacancies")
    with col2:
        render_kpi_card("Hiring Companies", f"{total_companies:,}", "🏢", "Unique organizations")
    with col3:
        render_kpi_card("Monitored Skills", f"{total_skills:,}", "🛠️", "Distinct technologies")
        
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    
    col4, col5, col6 = st.columns(3)
    with col4:
        render_kpi_card("Average Annual Salary", avg_sal_str, "💰", "Weighted market rate")
    with col5:
        render_kpi_card("Top Hiring Location", top_city, "📍", "Most active hub")
    with col6:
        render_kpi_card("Most In-Demand Skill", top_skill, "🚀", "Highest listing frequency")
        
    st.markdown("---")
    
    # 3. Render charts
    col_left, col_right = st.columns(2)
    
    # Donut Chart for Industries
    with col_left:
        st.subheader("Jobs by Industry")
        ind_df = get_top_industries(limit=8)
        if not ind_df.empty:
            # Custom HSL-inspired palette for Plotly
            color_palette = ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A", "#19D3F3", "#FF6692", "#B6E880"]
            fig_ind = px.pie(
                ind_df, 
                values="Openings", 
                names="Industry", 
                hole=0.45,
                color_discrete_sequence=color_palette
            )
            fig_ind.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E0E0E0", size=12),
                margin=dict(t=10, b=10, l=10, r=10),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_ind, use_container_width=True)
        else:
            st.info("No industry data available.")
            
    # Bar Chart for Employment Types
    with col_right:
        st.subheader("Jobs by Employment Type")
        session = db_session()
        try:
            results = session.query(
                Job.employment_type,
                func.count(Job.job_id).label("count")
            ).group_by(Job.employment_type).all()
            emp_df = pd.DataFrame(results, columns=["Employment Type", "Count"])
        finally:
            session.close()
            
        if not emp_df.empty:
            fig_emp = px.bar(
                emp_df,
                x="Employment Type",
                y="Count",
                color="Employment Type",
                color_discrete_sequence=["#19D3F3", "#FFA15A", "#AB63FA", "#00CC96"]
            )
            fig_emp.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E0E0E0", size=12),
                margin=dict(t=10, b=10, l=10, r=10),
                xaxis=dict(showgrid=False, title=""),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Jobs Count"),
                showlegend=False
            )
            st.plotly_chart(fig_emp, use_container_width=True)
        else:
            st.info("No employment type data available.")
