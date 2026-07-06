import streamlit as st
import plotly.express as px
import pandas as pd
from database.postgres import db_session, Job
from analytics.hiring_analysis import (
    get_top_companies,
    get_top_locations,
    get_top_industries,
    get_top_roles
)


def get_filter_options():
    """Queries distinct values from database to populate streamlit filter widgets."""
    session = db_session()
    try:
        # Distinct locations
        locs = session.query(Job.location).distinct().filter(Job.location.isnot(None)).all()
        locations = ["All"] + sorted([l[0] for l in locs])
        
        # Distinct industries
        inds = session.query(Job.industry).distinct().filter(Job.industry.isnot(None)).all()
        industries = ["All"] + sorted([i[0] for i in inds])
        
        # Distinct experiences
        exps = session.query(Job.experience_level).distinct().filter(Job.experience_level.isnot(None)).all()
        experiences = ["All"] + sorted([e[0] for e in exps])
        
        return locations, industries, experiences
    finally:
        session.close()


def show_hiring_dashboard():
    """Renders the hiring trends page."""
    st.markdown("<h2 class='page-title'>Hiring Trends</h2>", unsafe_allow_html=True)
    st.markdown("<p class='page-subtitle'>Explore hiring activity across companies, industries, locations, and roles.</p>", unsafe_allow_html=True)
    
    # 1. Filters container
    st.markdown("<div class='filter-container'>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    locations, industries, experiences = get_filter_options()
    
    with col1:
        selected_location = st.selectbox("Location Filter", locations)
    with col2:
        selected_industry = st.selectbox("Industry Filter", industries)
    with col3:
        selected_experience = st.selectbox("Experience Filter", experiences)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    # 2. Query data based on filters
    df_companies = get_top_companies(10, selected_location, selected_industry, selected_experience)
    df_cities = get_top_locations(10, selected_location, selected_industry, selected_experience)
    df_inds = get_top_industries(10, selected_location, selected_industry, selected_experience)
    df_roles = get_top_roles(10, selected_location, selected_industry, selected_experience)
    
    # Check if there is data
    if df_companies.empty or df_cities.empty or df_inds.empty or df_roles.empty:
        st.warning("⚠️ No job listings match the selected filters. Please select different criteria.")
        return
        
    # 3. Plot Layout: 2x2 grid of charts
    row1_col1, row1_col2 = st.columns(2)
    
    # Top Hiring Companies (Horizontal Bar Chart)
    with row1_col1:
        st.subheader("Top 10 Hiring Companies")
        fig_comp = px.bar(
            df_companies.sort_values(by="Openings", ascending=True),
            x="Openings",
            y="Company",
            orientation="h",
            color="Openings",
            color_continuous_scale="Viridis"
        )
        fig_comp.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E0E0E0", size=11),
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Jobs Count"),
            yaxis=dict(title=""),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_comp, use_container_width=True)
        
    # Top Cities hiring (Horizontal Bar Chart)
    with row1_col2:
        st.subheader("Top Hiring Cities")
        fig_cities = px.bar(
            df_cities.sort_values(by="Openings", ascending=True),
            x="Openings",
            y="Location",
            orientation="h",
            color="Openings",
            color_continuous_scale="Plasma"
        )
        fig_cities.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E0E0E0", size=11),
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Jobs Count"),
            yaxis=dict(title=""),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_cities, use_container_width=True)
        
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    row2_col1, row2_col2 = st.columns(2)
    
    # Top Industries (Vertical Bar Chart)
    with row2_col1:
        st.subheader("Hiring Volume by Industry")
        fig_inds = px.bar(
            df_inds,
            x="Industry",
            y="Openings",
            color="Openings",
            color_continuous_scale="Bluered"
        )
        fig_inds.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E0E0E0", size=11),
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis=dict(showgrid=False, title="", tickangle=45),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Jobs Count"),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_inds, use_container_width=True)
        
    # Trending Roles / Top Roles (Vertical Bar Chart)
    with row2_col2:
        st.subheader("Top Demanded Job Roles")
        fig_roles = px.bar(
            df_roles,
            x="Role",
            y="Openings",
            color="Openings",
            color_continuous_scale="Cividis"
        )
        fig_roles.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E0E0E0", size=11),
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis=dict(showgrid=False, title="", tickangle=45),
            yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Jobs Count"),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_roles, use_container_width=True)
