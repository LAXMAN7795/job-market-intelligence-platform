import pandas as pd
from sqlalchemy import func, desc
from database.postgres import db_session, Job, Company


def apply_job_filters(query, location: str = None, industry: str = None, experience_level: str = None):
    """Helper to dynamically apply filters to a SQLAlchemy Job query."""
    if location and location != "All":
        query = query.filter(Job.location == location)
    if industry and industry != "All":
        query = query.filter(Job.industry == industry)
    if experience_level and experience_level != "All":
        query = query.filter(Job.experience_level == experience_level)
    return query


def get_top_companies(limit: int = 10, location: str = None, industry: str = None, experience_level: str = None) -> pd.DataFrame:
    """Returns top companies hiring based on job counts."""
    session = db_session()
    try:
        query = session.query(
            Company.company_name,
            func.count(Job.job_id).label("job_count")
        ).join(Job, Company.company_id == Job.company_id)
        
        query = apply_job_filters(query, location, industry, experience_level)
        
        results = query.group_by(Company.company_name) \
                       .order_by(desc("job_count")) \
                       .limit(limit) \
                       .all()
                       
        return pd.DataFrame(results, columns=["Company", "Openings"])
    finally:
        session.close()


def get_top_locations(limit: int = 10, location: str = None, industry: str = None, experience_level: str = None) -> pd.DataFrame:
    """Returns top job locations (cities)."""
    session = db_session()
    try:
        query = session.query(
            Job.location,
            func.count(Job.job_id).label("job_count")
        )
        
        query = apply_job_filters(query, location, industry, experience_level)
        
        results = query.group_by(Job.location) \
                       .order_by(desc("job_count")) \
                       .limit(limit) \
                       .all()
                       
        return pd.DataFrame(results, columns=["Location", "Openings"])
    finally:
        session.close()


def get_top_roles(limit: int = 10, location: str = None, industry: str = None, experience_level: str = None) -> pd.DataFrame:
    """Returns top hiring roles (job titles)."""
    session = db_session()
    try:
        query = session.query(
            Job.title.label("role"),
            func.count(Job.job_id).label("job_count")
        )
        
        query = apply_job_filters(query, location, industry, experience_level)
        
        results = query.group_by(Job.title) \
                       .order_by(desc("job_count")) \
                       .limit(limit) \
                       .all()
                       
        return pd.DataFrame(results, columns=["Role", "Openings"])
    finally:
        session.close()


def get_top_industries(limit: int = 10, location: str = None, industry: str = None, experience_level: str = None) -> pd.DataFrame:
    """Returns top industries hiring."""
    session = db_session()
    try:
        query = session.query(
            Job.industry,
            func.count(Job.job_id).label("job_count")
        )
        
        query = apply_job_filters(query, location, industry, experience_level)
        
        results = query.group_by(Job.industry) \
                       .order_by(desc("job_count")) \
                       .limit(limit) \
                       .all()
                       
        return pd.DataFrame(results, columns=["Industry", "Openings"])
    finally:
        session.close()
