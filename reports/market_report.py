import os
import logging
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from database.postgres import db_session, Job, Company, Skill, JobSkill
from analytics.hiring_analysis import get_top_locations, get_top_roles, get_top_industries
from analytics.skill_analysis import get_top_skills
from analytics.geography_analysis import get_remote_percentage

# Setup logging
logger = logging.getLogger("reports.market_report")

REPORT_DIR = "reports"
REPORT_FILE_NAME = "market_intelligence_report.md"
REPORT_PATH = os.path.join(REPORT_DIR, REPORT_FILE_NAME)


def calculate_highest_paying_skill() -> tuple[str, float]:
    """
    Calculates the skill associated with the highest average salary.
    """
    session = db_session()
    try:
        result = session.query(
            Skill.skill_name,
            func.avg((Job.salary_min + Job.salary_max) / 2).label("avg_salary")
        ).join(JobSkill, Skill.skill_id == JobSkill.skill_id) \
         .join(Job, JobSkill.job_id == Job.job_id) \
         .filter(Job.salary_min.isnot(None), Job.salary_max.isnot(None)) \
         .group_by(Skill.skill_name) \
         .order_by(desc("avg_salary")) \
         .first()
         
        if result:
            return result[0], round(float(result[1]), 1)
        return "N/A", 0.0
    finally:
        session.close()


def calculate_fastest_growing_role() -> str:
    """
    Calculates the 'fastest growing role' by selecting the job title
    with the highest volume of postings in the most recent 30-day window.
    """
    session = db_session()
    try:
        # Find latest date in DB
        latest_date_query = session.query(func.max(Job.posted_date)).scalar()
        if not latest_date_query:
            return "N/A"
            
        cutoff_date = latest_date_query - timedelta(days=30)
        
        result = session.query(
            Job.title,
            func.count(Job.job_id).label("count")
        ).filter(Job.posted_date >= cutoff_date) \
         .group_by(Job.title) \
         .order_by(desc("count")) \
         .first()
         
        if result:
            return result[0]
            
        # Fallback to general top role if no recent posts
        fallback = session.query(
            Job.title,
            func.count(Job.job_id).label("count")
        ).group_by(Job.title) \
         .order_by(desc("count")) \
         .first()
         
        return fallback[0] if fallback else "N/A"
    finally:
        session.close()


def generate_market_report() -> dict:
    """
    Queries database metrics to compile key market intelligence metrics.
    Writes the report to reports/market_intelligence_report.md and returns the metrics.
    """
    logger.info("Generating Market Intelligence Report...")
    
    # 1. Fetch Stats
    loc_df = get_top_locations(limit=1)
    top_city = loc_df.iloc[0]["Location"] if not loc_df.empty else "N/A"
    
    skill_df = get_top_skills(limit=1)
    top_skill = skill_df.iloc[0]["Skill"] if not skill_df.empty else "N/A"
    
    industry_df = get_top_industries(limit=1)
    top_industry = industry_df.iloc[0]["Industry"] if not industry_df.empty else "N/A"
    
    fastest_growing_role = calculate_fastest_growing_role()
    highest_paying_skill, avg_pay = calculate_highest_paying_skill()
    remote_pct = get_remote_percentage()
    
    # Session counts
    session = db_session()
    total_jobs = session.query(func.count(Job.job_id)).scalar() or 0
    total_companies = session.query(func.count(Company.company_id)).scalar() or 0
    session.close()
    
    metrics = {
        "top_city": top_city,
        "top_skill": top_skill,
        "top_industry": top_industry,
        "fastest_growing_role": fastest_growing_role,
        "highest_paying_skill": f"{highest_paying_skill} ({avg_pay} LPA)",
        "remote_percentage": f"{remote_pct}%",
        "total_jobs": total_jobs,
        "total_companies": total_companies,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 2. Format Markdown text
    markdown_content = f"""# Market Intelligence Report

**Generated on:** {metrics['generated_at']}  
**Data Scope:** Ingested jobs from The Muse API & Kaggle Historical Dataset  

---

## Executive Highlights

*   **Total Jobs Analyzed:** {metrics['total_jobs']}
*   **Total Hiring Companies:** {metrics['total_companies']}

---

## Core Market Indicators

| Indicator | Value |
| :--- | :--- |
| **Top Hiring City** | {metrics['top_city']} |
| **Most Demanded Skill** | {metrics['top_skill']} |
| **Top Industry** | {metrics['top_industry']} |
| **Fastest Growing Role** | {metrics['fastest_growing_role']} |
| **Highest Paying Skill** | {metrics['highest_paying_skill']} |
| **Remote Job Percentage** | {metrics['remote_percentage']} |

---

## Key Insights

1. **Tech Hub Dominance**: **{metrics['top_city']}** continues to lead hiring activity, acting as the primary hub for employment opportunities within the database scope.
2. **Skill Capitalization**: Proficiency in **{metrics['top_skill']}** represents the highest frequency demand across multiple roles, making it a critical skill for prospective candidates.
3. **Remote Accessibility**: At **{metrics['remote_percentage']}** remote opportunities, the market shows a healthy spread of flexible work options, though onsite/hybrid settings remain substantial.
4. **Compensation Premium**: Jobs listing **{highest_paying_skill}** command the highest financial premium, yielding an average salary rate of **{avg_pay} LPA**.
"""

    os.makedirs(REPORT_DIR, exist_ok=True)
    try:
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        logger.info(f"Market Report successfully written to {REPORT_PATH}")
    except Exception as e:
        logger.error(f"Error writing Market Report: {e}", exc_info=True)
        raise e
        
    return metrics


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    metrics = generate_market_report()
    print(metrics)
