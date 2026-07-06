import streamlit as st
import plotly.express as px
import pandas as pd
from database.postgres import db_session, Job
from analytics.skill_analysis import get_top_skills, get_skill_frequency, get_skill_rankings


def get_skill_filter_options():
    """Fetches unique roles and industries to populate filters."""
    session = db_session()
    try:
        # Distinct roles
        roles_raw = session.query(Job.title).distinct().filter(Job.title.isnot(None)).all()
        roles = ["All"] + sorted([r[0] for r in roles_raw])
        
        # Distinct industries
        inds_raw = session.query(Job.industry).distinct().filter(Job.industry.isnot(None)).all()
        industries = ["All"] + sorted([i[0] for i in inds_raw])
        
        return roles, industries
    finally:
        session.close()


def show_skill_dashboard():
    """Renders the skill intelligence dashboard page."""
    st.markdown("<h2 class='page-title'>Skill Intelligence</h2>", unsafe_allow_html=True)
    st.markdown("<p class='page-subtitle'>Analyze tech stacks and demand frequencies across roles and industries.</p>", unsafe_allow_html=True)
    
    # 1. Filters
    st.markdown("<div class='filter-container'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    roles, industries = get_skill_filter_options()
    
    with col1:
        selected_role = st.selectbox("Role Filter", roles)
    with col2:
        selected_industry = st.selectbox("Industry Filter", industries)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    # 2. Get Data
    df_top = get_top_skills(20, selected_role, selected_industry)
    df_freq = get_skill_frequency(selected_role, selected_industry)
    df_ranks = get_skill_rankings(selected_role, selected_industry)
    
    if df_top.empty or df_freq.empty:
        st.warning("⚠️ No skill associations match the selected filters.")
        return
        
    # Helper to retrieve frequency % for a skill
    def get_skill_pct(skill_name):
        row = df_freq[df_freq["Skill"] == skill_name]
        return row.iloc[0]["Frequency %"] if not row.empty else 0.0

    # 3. Dynamic Category Cards (Python, SQL, Cloud, AI/Big Data)
    py_pct = get_skill_pct("Python")
    sql_pct = get_skill_pct("SQL")
    
    # Cloud is AWS + Azure average (or max)
    aws_pct = get_skill_pct("AWS")
    azure_pct = get_skill_pct("Azure")
    cloud_pct = round(max(aws_pct, azure_pct), 1)
    
    # Big Data / DevOps is Spark + Docker average
    spark_pct = get_skill_pct("Spark")
    docker_pct = get_skill_pct("Docker")
    ai_pct = round(max(spark_pct, docker_pct), 1)
    
    # Display Key tech demand cards
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown(
            f"""
            <div class="skill-indicator-card py-card">
                <div class="skill-name">🐍 Python Demand</div>
                <div class="skill-pct">{py_pct}%</div>
                <div class="skill-desc">of matched listings</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            f"""
            <div class="skill-indicator-card sql-card">
                <div class="skill-name">🗄️ SQL Demand</div>
                <div class="skill-pct">{sql_pct}%</div>
                <div class="skill-desc">of matched listings</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c3:
        st.markdown(
            f"""
            <div class="skill-indicator-card cloud-card">
                <div class="skill-name">☁️ Cloud Demand</div>
                <div class="skill-pct">{cloud_pct}%</div>
                <div class="skill-desc">AWS / Azure penetration</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c4:
        st.markdown(
            f"""
            <div class="skill-indicator-card ai-card">
                <div class="skill-name">🐳 DevOps/Big Data</div>
                <div class="skill-pct">{ai_pct}%</div>
                <div class="skill-desc">Docker / Spark penetration</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
    st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
    
    # 4. Plots: Top 20 Skills & Rank Table
    col_chart, col_table = st.columns([3, 2])
    
    with col_chart:
        st.subheader("Top 20 Demanded Tech Skills")
        fig_skills = px.bar(
            df_top.sort_values(by="Demand Count", ascending=True),
            x="Demand Count",
            y="Skill",
            orientation="h",
            color="Demand Count",
            color_continuous_scale="Teal"
        )
        fig_skills.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E0E0E0", size=11),
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Jobs listing this skill"),
            yaxis=dict(title=""),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_skills, use_container_width=True)
        
    with col_table:
        st.subheader("Skill Demand Ranking")
        st.markdown(
            """
            <style>
            .streamlit-table {
                font-family: 'Inter', sans-serif;
                background-color: transparent !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        # Render a clean styled dataframe
        st.dataframe(
            df_ranks.rename(columns={
                "Rank": "Rank", 
                "Skill": "Technology", 
                "Demand Count": "Count", 
                "Frequency %": "Market Share"
            }),
            use_container_width=True,
            hide_index=True
        )
