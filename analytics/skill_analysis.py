import pandas as pd
from sqlalchemy import func, desc
from database.postgres import db_session, Job, Skill, JobSkill


def apply_skill_job_filters(query, role: str = None, industry: str = None):
    """Applies role (job title) and industry filters to a query joined on Job."""
    if role and role != "All":
        query = query.filter(Job.title == role)
    if industry and industry != "All":
        query = query.filter(Job.industry == industry)
    return query


def get_top_skills(limit: int = 20, role: str = None, industry: str = None) -> pd.DataFrame:
    """
    Returns the top skills demanded based on job associations.
    Allows filtering by role (job title) and industry.
    """
    session = db_session()
    try:
        query = session.query(
            Skill.skill_name,
            func.count(JobSkill.id).label("demand_count")
        ).join(JobSkill, Skill.skill_id == JobSkill.skill_id) \
         .join(Job, JobSkill.job_id == Job.job_id)
         
        query = apply_skill_job_filters(query, role, industry)
        
        results = query.group_by(Skill.skill_name) \
                       .order_by(desc("demand_count")) \
                       .limit(limit) \
                       .all()
                       
        return pd.DataFrame(results, columns=["Skill", "Demand Count"])
    finally:
        session.close()


def get_skill_frequency(role: str = None, industry: str = None) -> pd.DataFrame:
    """
    Calculates the frequency of each skill as a percentage of total jobs.
    Allows filtering by role and industry.
    """
    session = db_session()
    try:
        # Get total job count under the specified filters
        total_jobs_query = session.query(func.count(Job.job_id))
        if role and role != "All":
            total_jobs_query = total_jobs_query.filter(Job.title == role)
        if industry and industry != "All":
            total_jobs_query = total_jobs_query.filter(Job.industry == industry)
            
        total_jobs = total_jobs_query.scalar() or 0
        
        # Get skill counts
        query = session.query(
            Skill.skill_name,
            func.count(JobSkill.id).label("demand_count")
        ).join(JobSkill, Skill.skill_id == JobSkill.skill_id) \
         .join(Job, JobSkill.job_id == Job.job_id)
         
        query = apply_skill_job_filters(query, role, industry)
        results = query.group_by(Skill.skill_name).all()
        
        df = pd.DataFrame(results, columns=["Skill", "Demand Count"])
        
        if total_jobs > 0:
            df["Frequency %"] = (df["Demand Count"] / total_jobs * 100).round(1)
        else:
            df["Frequency %"] = 0.0
            
        return df.sort_values(by="Demand Count", ascending=False)
    finally:
        session.close()


def get_skill_rankings(role: str = None, industry: str = None) -> pd.DataFrame:
    """
    Returns rankings of all skills based on demand count.
    """
    df = get_skill_frequency(role, industry)
    df["Rank"] = df["Demand Count"].rank(ascending=False, method="min").astype(int)
    return df[["Rank", "Skill", "Demand Count", "Frequency %"]].sort_values(by="Rank")
