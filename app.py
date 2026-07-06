import os
import streamlit as st

# Set page config as the very first Streamlit command
st.set_page_config(
    page_title="Job Market Intelligence Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling injection
def inject_custom_css():
    st.markdown(
        """
        <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@300;400;500;600;700;800&display=swap');
        
        /* Global Styles */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }
        
        .main-header {
            font-family: 'Outfit', sans-serif;
            font-weight: 800;
            background: linear-gradient(135deg, #19D3F3 0%, #AB63FA 50%, #EF553B 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.8rem;
            margin-bottom: 0.2rem;
            text-align: left;
        }
        
        .page-title {
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
            color: #FFFFFF;
            font-size: 2rem;
            margin-bottom: 5px;
        }
        
        .page-subtitle {
            color: #9CA3AF;
            font-size: 1.1rem;
            margin-bottom: 25px;
        }
        
        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #0B0F19 !important;
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        /* KPI Cards Styling */
        .kpi-card {
            background: rgba(17, 24, 39, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.2);
            transition: transform 0.2s, border-color 0.2s;
        }
        .kpi-card:hover {
            transform: translateY(-2px);
            border-color: rgba(25, 211, 243, 0.4);
        }
        .kpi-card-header {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        .kpi-card-icon {
            font-size: 1.5rem;
            margin-right: 10px;
        }
        .kpi-card-title {
            color: #9CA3AF;
            font-size: 0.9rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .kpi-card-value {
            font-family: 'Outfit', sans-serif;
            font-size: 1.8rem;
            font-weight: 700;
            color: #FFFFFF;
        }
        .kpi-card-desc {
            color: #6B7280;
            font-size: 0.75rem;
            margin-top: 5px;
        }
        
        /* Skill Indicator Cards */
        .skill-indicator-card {
            border-radius: 12px;
            padding: 15px;
            color: #FFFFFF;
            text-align: center;
            box-shadow: 0 4px 15px 0 rgba(0,0,0,0.15);
            border: 1px solid rgba(255,255,255,0.05);
        }
        .py-card { background: linear-gradient(135deg, rgba(53, 114, 239, 0.2) 0%, rgba(53, 114, 239, 0.05) 100%); border-left: 4px solid #3572EF; }
        .sql-card { background: linear-gradient(135deg, rgba(0, 204, 150, 0.2) 0%, rgba(0, 204, 150, 0.05) 100%); border-left: 4px solid #00CC96; }
        .cloud-card { background: linear-gradient(135deg, rgba(171, 99, 250, 0.2) 0%, rgba(171, 99, 250, 0.05) 100%); border-left: 4px solid #AB63FA; }
        .ai-card { background: linear-gradient(135deg, rgba(239, 85, 59, 0.2) 0%, rgba(239, 85, 59, 0.05) 100%); border-left: 4px solid #EF553B; }
        
        .skill-name {
            font-size: 0.95rem;
            font-weight: 600;
            margin-bottom: 5px;
            color: #E5E7EB;
        }
        .skill-pct {
            font-family: 'Outfit', sans-serif;
            font-size: 2rem;
            font-weight: 800;
            color: #FFFFFF;
        }
        .skill-desc {
            font-size: 0.75rem;
            color: #9CA3AF;
            margin-top: 3px;
        }
        
        /* Filter Container Styles */
        .filter-container {
            background-color: rgba(31, 41, 55, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 15px 25px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# Inject styling
inject_custom_css()

# Dashboard Title
st.markdown("<h1 class='main-header'>Market Intelligence Platform</h1>", unsafe_allow_html=True)
st.markdown("<div style='height: 5px; margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# Import sub-dashboards
from dashboard.executive_dashboard import show_executive_dashboard
from dashboard.hiring_dashboard import show_hiring_dashboard
from dashboard.skill_dashboard import show_skill_dashboard
from dashboard.salary_dashboard import show_salary_dashboard
from dashboard.geography_dashboard import show_geography_dashboard
from reports.market_report import generate_market_report, REPORT_PATH

# Sidebar Navigation Layout
st.sidebar.markdown(
    """
    <div style='text-align: center; margin-bottom: 20px;'>
        <h2 style='color: #FFFFFF; font-family: Outfit; font-weight: 700; margin-bottom: 5px;'>Navigation</h2>
        <span style='color: #6B7280; font-size: 0.85rem;'>Choose an analytics page</span>
    </div>
    """, 
    unsafe_allow_html=True
)

navigation_page = st.sidebar.radio(
    "Go To:",
    [
        "Executive Summary",
        "Hiring Trends",
        "Skill Intelligence",
        "Salary Intelligence",
        "Geographic Intelligence",
        "Market Intelligence Report"
    ],
    label_visibility="collapsed"
)

# Route to active sub-page
if navigation_page == "Executive Summary":
    show_executive_dashboard()
    
elif navigation_page == "Hiring Trends":
    show_hiring_dashboard()
    
elif navigation_page == "Skill Intelligence":
    show_skill_dashboard()
    
elif navigation_page == "Salary Intelligence":
    show_salary_dashboard()
    
elif navigation_page == "Geographic Intelligence":
    show_geography_dashboard()
    
elif navigation_page == "Market Intelligence Report":
    st.markdown("<h2 class='page-title'>Market Intelligence Report</h2>", unsafe_allow_html=True)
    st.markdown("<p class='page-subtitle'>Summarized market findings, updated dynamically from the database.</p>", unsafe_allow_html=True)
    
    # Check if report exists, if not, generate it
    if not os.path.exists(REPORT_PATH):
        st.info("🔄 First run detected. Compiling database metrics for report generation...")
        try:
            generate_market_report()
        except Exception as e:
            st.error(f"Error compiling database records: {e}")
            
    if os.path.exists(REPORT_PATH):
        with open(REPORT_PATH, "r", encoding="utf-8") as f:
            report_markdown = f.read()
        # Render markdown directly
        st.markdown(report_markdown)
    else:
        st.error("⚠️ Failed to generate or locate the market report file. Please verify database records exist.")
