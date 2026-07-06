import streamlit as st
import plotly.express as px
import pandas as pd
from analytics.geography_analysis import get_jobs_by_city, get_remote_distribution


# Map coordinate lookup for common cities in our dataset
CITY_COORDINATES = {
    "Bangalore": (12.9716, 77.5946),
    "Mumbai": (19.0760, 72.8777),
    "Hyderabad": (17.3850, 78.4867),
    "Pune": (18.5204, 73.8567),
    "Chennai": (13.0827, 80.2707),
    "Noida": (28.5355, 77.3910),
    "Gurgaon": (28.4595, 77.0266),
    "Delhi NCR": (28.6139, 77.2090),
    "New York": (40.7128, -74.0060),
    "Sarasota": (27.3364, -82.5307),
    "San Francisco": (37.7749, -122.4194),
}


def build_map_dataframe(df_cities: pd.DataFrame) -> pd.DataFrame:
    """Maps city names to latitude and longitude coordinates for map plotting."""
    map_data = []
    
    for _, row in df_cities.iterrows():
        city = row["City"]
        openings = row["Openings"]
        
        # Check map coordinates
        if city in CITY_COORDINATES:
            lat, lon = CITY_COORDINATES[city]
            map_data.append({
                "city": city,
                "lat": lat,
                "lon": lon,
                "Openings": openings,
                # Scaling factor for circle size in st.map
                "radius": float(openings) * 100
            })
            
    return pd.DataFrame(map_data)


def show_geography_dashboard():
    """Renders the geographic intelligence dashboard page."""
    st.markdown("<h2 class='page-title'>Geographic Intelligence</h2>", unsafe_allow_html=True)
    st.markdown("<p class='page-subtitle'>Understand spatial hiring distributions and flexible work options across locations.</p>", unsafe_allow_html=True)
    
    # Get geography data
    df_cities = get_jobs_by_city()
    df_remote = get_remote_distribution()
    
    if df_cities.empty:
        st.info("ℹ️ No geographic data is currently available. Run the ETL pipeline to ingest listings.")
        return
        
    # 1. Map visualization
    st.subheader("Job Openings Geographic Map")
    df_map = build_map_dataframe(df_cities)
    
    if not df_map.empty:
        # Streamlit interactive native map
        st.map(df_map, latitude="lat", longitude="lon", size="radius", color="#19D3F3")
        st.caption("Interactive map visualizing job distributions across major hubs. Bubble size is proportional to job volume.")
    else:
        st.warning("⚠️ Could not map coordinate mappings for the current set of locations in the database.")
        
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    # 2. Split layout: City list & Remote breakdown
    col_list, col_remote = st.columns(2)
    
    with col_list:
        st.subheader("Openings by City")
        fig_cities = px.bar(
            df_cities.head(10).sort_values("Openings", ascending=True),
            x="Openings",
            y="City",
            orientation="h",
            color="Openings",
            color_continuous_scale="Mint"
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
        
    with col_remote:
        st.subheader("Remote vs Hybrid vs Onsite")
        if not df_remote.empty:
            fig_pie = px.pie(
                df_remote,
                values="Count",
                names="Remote Type",
                hole=0.4,
                color="Remote Type",
                color_discrete_map={
                    "Remote": "#00CC96",
                    "Hybrid": "#FFA15A",
                    "Onsite": "#EF553B"
                }
            )
            fig_pie.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E0E0E0", size=11),
                margin=dict(t=10, b=10, l=10, r=10),
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No remote type classification data available.")
