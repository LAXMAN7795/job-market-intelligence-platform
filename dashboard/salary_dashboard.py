import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from analytics.salary_analysis import (
    get_salary_distribution,
    get_salary_by_role,
    get_salary_by_location,
    get_salary_by_experience
)


def show_salary_dashboard():
    """Renders the salary intelligence dashboard page."""
    st.markdown("<h2 class='page-title'>Salary Intelligence</h2>", unsafe_allow_html=True)
    st.markdown("<p class='page-subtitle'>Analyze compensation distributions, benchmarks, and trends across the market.</p>", unsafe_allow_html=True)
    
    # Get analytical data
    df_dist = get_salary_distribution()
    df_role = get_salary_by_role(10)
    df_loc = get_salary_by_location(10)
    df_exp = get_salary_by_experience()
    
    if df_dist.empty:
        st.info("ℹ️ No salary information is available in the database yet. Ingest and process Kaggle jobs to populate salary metrics.")
        return
        
    # Calculate average for reference line
    avg_salary = df_dist["Average Salary"].mean()
    
    # 1. Salary Distribution Histogram
    st.subheader("Market Salary Distribution (LPA)")
    fig_dist = px.histogram(
        df_dist,
        x="Average Salary",
        nbins=25,
        color_discrete_sequence=["#AB63FA"],
        labels={"Average Salary": "Salary (LPA)"}
    )
    # Add line for average
    fig_dist.add_vline(
        x=avg_salary,
        line_dash="dash",
        line_color="#00CC96",
        annotation_text=f"Average: {avg_salary:.1f} LPA",
        annotation_position="top right"
    )
    fig_dist.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E0E0E0", size=11),
        margin=dict(t=30, b=10, l=10, r=10),
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Jobs Count")
    )
    st.plotly_chart(fig_dist, use_container_width=True)
    
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    # 2. Row of details: Role & City
    col_role, col_city = st.columns(2)
    
    with col_role:
        st.subheader("Highest Paying Roles (Average LPA)")
        fig_role = px.bar(
            df_role.sort_values("Average Salary", ascending=True),
            x="Average Salary",
            y="Role",
            orientation="h",
            color="Average Salary",
            color_continuous_scale="Purples",
            hover_data=["Min Salary", "Max Salary", "Job Count"]
        )
        fig_role.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E0E0E0", size=11),
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Salary (LPA)"),
            yaxis=dict(title=""),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_role, use_container_width=True)
        
    with col_city:
        st.subheader("Salary Benchmarks by City")
        fig_city = px.bar(
            df_loc.sort_values("Average Salary", ascending=True),
            x="Average Salary",
            y="Location",
            orientation="h",
            color="Average Salary",
            color_continuous_scale="Teal",
            hover_data=["Min Salary", "Max Salary"]
        )
        fig_city.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E0E0E0", size=11),
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Salary (LPA)"),
            yaxis=dict(title=""),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_city, use_container_width=True)
        
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    # 3. Experience Benchmarks (Box plot of salaries using raw distribution data)
    st.subheader("Salary Ranges by Experience Level")
    
    # Box plot from raw dataset distribution
    # Sort order to align Box plot series logically
    sort_order = {"Fresher": 0, "0-2 Years": 1, "2-5 Years": 2, "5+ Years": 3}
    df_dist_sorted = df_dist.copy()
    df_dist_sorted["sort_key"] = df_dist_sorted["Experience Level"].map(sort_order).fillna(4)
    df_dist_sorted = df_dist_sorted.sort_values("sort_key")
    
    fig_box = px.box(
        df_dist_sorted,
        x="Experience Level",
        y="Average Salary",
        color="Experience Level",
        color_discrete_sequence=["#19D3F3", "#00CC96", "#FFA15A", "#EF553B"]
    )
    fig_box.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E0E0E0", size=11),
        margin=dict(t=10, b=10, l=10, r=10),
        xaxis=dict(title=""),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Salary (LPA)"),
        showlegend=False
    )
    st.plotly_chart(fig_box, use_container_width=True)
