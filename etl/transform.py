import re
import logging
import pandas as pd
import numpy as np

# Setup logging
logger = logging.getLogger("etl.transform")

# Pre-defined skills and their regex patterns for boundary-safe case-insensitive matching
SKILL_PATTERNS = {
    "Python": re.compile(r"\bpython\b", re.IGNORECASE),
    "SQL": re.compile(r"\bsql\b", re.IGNORECASE),
    "Power BI": re.compile(r"\bpower\s*bi\b", re.IGNORECASE),
    "Tableau": re.compile(r"\btableau\b", re.IGNORECASE),
    "Excel": re.compile(r"\bexcel\b", re.IGNORECASE),
    "AWS": re.compile(r"\baws\b|\bamazon\s+web\s+services\b", re.IGNORECASE),
    "Azure": re.compile(r"\bazure\b", re.IGNORECASE),
    "Spark": re.compile(r"\bspark\b|\bpyspark\b", re.IGNORECASE),
    "Docker": re.compile(r"\bdocker\b", re.IGNORECASE)
}


def classify_salary_bucket(salary_min: float | None, salary_max: float | None) -> str:
    """
    Classifies a job listing into a salary bucket based on its average salary.
    Buckets: '0-5 LPA', '5-10 LPA', '10-15 LPA', '15+ LPA', or 'Not Specified'.
    """
    if pd.isna(salary_min) and pd.isna(salary_max):
        return "Not Specified"
        
    # Use average if both exist, otherwise use whichever is present
    vals = [v for v in [salary_min, salary_max] if pd.notna(v) and v is not None]
    if not vals:
        return "Not Specified"
        
    avg_salary = sum(vals) / len(vals)
    
    if avg_salary <= 5.0:
        return "0-5 LPA"
    elif avg_salary <= 10.0:
        return "5-10 LPA"
    elif avg_salary <= 15.0:
        return "10-15 LPA"
    else:
        return "15+ LPA"


def classify_experience_bucket(exp_str: str) -> str:
    """
    Classifies raw experience text into one of the standardized buckets:
    - Fresher
    - 0-2 Years
    - 2-5 Years
    - 5+ Years
    """
    if pd.isna(exp_str) or not isinstance(exp_str, str):
        return "0-2 Years"
        
    s = exp_str.lower().strip()
    
    if "fresher" in s or "no experience" in s:
        return "Fresher"
    elif "0-2" in s or "1 year" in s or "2 years" in s:
        return "0-2 Years"
    elif "2-5" in s or "3 years" in s or "4 years" in s or "5 years" in s:
        return "2-5 Years"
    elif "5+" in s or "senior" in s or "lead" in s or "6 years" in s or "7 years" in s or "manager" in s:
        return "5+ Years"
    else:
        # Fallback parsing for integers
        match = re.search(r"(\d+)\s*-?\s*(\d*)\s*years?", s)
        if match:
            try:
                min_years = int(match.group(1))
                if min_years == 0:
                    return "Fresher"
                elif min_years <= 2:
                    return "0-2 Years"
                elif min_years <= 5:
                    return "2-5 Years"
                else:
                    return "5+ Years"
            except ValueError:
                pass
        return "0-2 Years"


def classify_remote_type(location: str, title: str, current_remote: str = "Onsite") -> str:
    """
    Classifies a job as Remote, Hybrid, or Onsite based on location, title, and metadata.
    """
    # If the cleaning step already identified it as Remote, keep it
    if current_remote == "Remote":
        return "Remote"
        
    loc = str(location).lower()
    t = str(title).lower()
    
    if "remote" in loc or "remote" in t:
        return "Remote"
    elif "hybrid" in loc or "hybrid" in t:
        return "Hybrid"
    elif "work from home" in loc or "wfh" in loc or "wfh" in t:
        return "Remote"
    else:
        return "Onsite"


def extract_skills_from_text(description: str, raw_skills_field: str) -> list[str]:
    """
    Extracts matching technologies from the job description text and the raw skills field.
    """
    combined_text = f"{description} {raw_skills_field}"
    extracted_skills = []
    
    for skill, pattern in SKILL_PATTERNS.items():
        if pattern.search(combined_text):
            extracted_skills.append(skill)
            
    return extracted_skills


def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Performs data enrichment, adding experience, salary, remote, and skill columns.
    """
    logger.info("Transforming DataFrame fields...")
    df_transformed = df.copy()
    
    # 1. Apply Experience Bucket Classification
    df_transformed["experience_level"] = df_transformed["experience_level"].apply(classify_experience_bucket)
    
    # 2. Apply Salary Bucket Classification
    df_transformed["salary_bucket"] = df_transformed.apply(
        lambda r: classify_salary_bucket(r["salary_min"], r["salary_max"]),
        axis=1
    )
    
    # 3. Apply Remote Classification
    df_transformed["remote_type"] = df_transformed.apply(
        lambda r: classify_remote_type(r["location"], r["title"], r["remote_type"]),
        axis=1
    )
    
    # 4. Extract Skills List
    df_transformed["extracted_skills"] = df_transformed.apply(
        lambda r: extract_skills_from_text(str(r["description"]), str(r["skills_raw"])),
        axis=1
    )
    
    # Count skills extracted for tracking
    total_skills_extracted = df_transformed["extracted_skills"].apply(len).sum()
    logger.info(f"Transformation complete. Extracted {total_skills_extracted} total skills across listings.")
    
    return df_transformed
