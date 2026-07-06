import pandas as pd
from sqlalchemy import func, desc
from database.postgres import db_session, Job


def get_jobs_by_city() -> pd.DataFrame:
    """Returns total job openings grouped by city location, sorted descending."""
    session = db_session()
    try:
        results = session.query(
            Job.location.label("city"),
            func.count(Job.job_id).label("job_count")
        ).group_by(Job.location) \
         .order_by(desc("job_count")) \
         .all()
         
        return pd.DataFrame(results, columns=["City", "Openings"])
    finally:
        session.close()


def get_remote_distribution() -> pd.DataFrame:
    """Helper function to get counts of Remote, Hybrid, and Onsite jobs."""
    session = db_session()
    try:
        results = session.query(
            Job.remote_type,
            func.count(Job.job_id).label("count")
        ).group_by(Job.remote_type).all()
        
        return pd.DataFrame(results, columns=["Remote Type", "Count"])
    finally:
        session.close()


def _get_percentage_for_type(remote_type_name: str) -> float:
    """Calculates the percentage of jobs matching a specific remote type."""
    session = db_session()
    try:
        total_jobs = session.query(func.count(Job.job_id)).scalar() or 0
        if total_jobs == 0:
            return 0.0
            
        type_jobs = session.query(func.count(Job.job_id)) \
                           .filter(Job.remote_type == remote_type_name) \
                           .scalar() or 0
                           
        return round((type_jobs / total_jobs) * 100, 1)
    finally:
        session.close()


def get_remote_percentage() -> float:
    """Returns the percentage of jobs classified as Remote."""
    return _get_percentage_for_type("Remote")


def get_hybrid_percentage() -> float:
    """Returns the percentage of jobs classified as Hybrid."""
    return _get_percentage_for_type("Hybrid")


def get_onsite_percentage() -> float:
    """Returns the percentage of jobs classified as Onsite."""
    return _get_percentage_for_type("Onsite")
