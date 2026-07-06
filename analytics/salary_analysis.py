import pandas as pd
from sqlalchemy import func, desc
from database.postgres import db_session, Job


def get_salary_distribution() -> pd.DataFrame:
    """
    Returns job records containing valid (non-null) salary bounds
    for histogram and statistical visualization.
    """
    session = db_session()
    try:
        # Query jobs with valid salary fields
        results = session.query(
            Job.title,
            Job.location,
            Job.industry,
            Job.experience_level,
            Job.salary_min,
            Job.salary_max
        ).filter(Job.salary_min.isnot(None), Job.salary_max.isnot(None)).all()
        
        df = pd.DataFrame(results, columns=["Role", "Location", "Industry", "Experience Level", "Salary Min", "Salary Max"])
        # Add average salary helper column in LPA
        df["Average Salary"] = (df["Salary Min"] + df["Salary Max"]) / 2
        return df
    finally:
        session.close()


def get_average_salary() -> float:
    """Returns the overall average salary (in LPA) across all listed jobs with salary values."""
    session = db_session()
    try:
        # Calculate overall average of (salary_min + salary_max) / 2
        avg_val = session.query(
            func.avg((Job.salary_min + Job.salary_max) / 2)
        ).filter(Job.salary_min.isnot(None), Job.salary_max.isnot(None)).scalar()
        
        return round(float(avg_val), 2) if avg_val is not None else 0.0
    finally:
        session.close()


def get_salary_by_role(limit: int = 10) -> pd.DataFrame:
    """
    Returns average, min, and max salary grouped by job title/role.
    """
    session = db_session()
    try:
        results = session.query(
            Job.title.label("role"),
            func.avg((Job.salary_min + Job.salary_max) / 2).label("avg_salary"),
            func.min(Job.salary_min).label("min_salary"),
            func.max(Job.salary_max).label("max_salary"),
            func.count(Job.job_id).label("job_count")
        ).filter(Job.salary_min.isnot(None), Job.salary_max.isnot(None)) \
         .group_by(Job.title) \
         .order_by(desc("avg_salary")) \
         .limit(limit) \
         .all()
         
        df = pd.DataFrame(results, columns=["Role", "Average Salary", "Min Salary", "Max Salary", "Job Count"])
        # Round numeric values
        df["Average Salary"] = df["Average Salary"].round(1)
        df["Min Salary"] = df["Min Salary"].round(1)
        df["Max Salary"] = df["Max Salary"].round(1)
        return df
    finally:
        session.close()


def get_salary_by_location(limit: int = 10) -> pd.DataFrame:
    """
    Returns average, min, and max salary grouped by location.
    """
    session = db_session()
    try:
        results = session.query(
            Job.location,
            func.avg((Job.salary_min + Job.salary_max) / 2).label("avg_salary"),
            func.min(Job.salary_min).label("min_salary"),
            func.max(Job.salary_max).label("max_salary")
        ).filter(Job.salary_min.isnot(None), Job.salary_max.isnot(None)) \
         .group_by(Job.location) \
         .order_by(desc("avg_salary")) \
         .limit(limit) \
         .all()
         
        df = pd.DataFrame(results, columns=["Location", "Average Salary", "Min Salary", "Max Salary"])
        df["Average Salary"] = df["Average Salary"].round(1)
        df["Min Salary"] = df["Min Salary"].round(1)
        df["Max Salary"] = df["Max Salary"].round(1)
        return df
    finally:
        session.close()


def get_salary_by_experience() -> pd.DataFrame:
    """
    Returns average, min, and max salary grouped by experience level.
    """
    session = db_session()
    try:
        results = session.query(
            Job.experience_level,
            func.avg((Job.salary_min + Job.salary_max) / 2).label("avg_salary"),
            func.min(Job.salary_min).label("min_salary"),
            func.max(Job.salary_max).label("max_salary")
        ).filter(Job.salary_min.isnot(None), Job.salary_max.isnot(None)) \
         .group_by(Job.experience_level) \
         .all()
         
        df = pd.DataFrame(results, columns=["Experience Level", "Average Salary", "Min Salary", "Max Salary"])
        df["Average Salary"] = df["Average Salary"].round(1)
        df["Min Salary"] = df["Min Salary"].round(1)
        df["Max Salary"] = df["Max Salary"].round(1)
        
        # Sort values logically based on typical experience hierarchy
        sort_order = {"Fresher": 0, "0-2 Years": 1, "2-5 Years": 2, "5+ Years": 3}
        df["sort_key"] = df["Experience Level"].map(sort_order).fillna(4)
        df = df.sort_values("sort_key").drop(columns=["sort_key"])
        
        return df
    finally:
        session.close()
