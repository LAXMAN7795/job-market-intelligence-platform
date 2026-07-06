import re
import logging
import pandas as pd
import numpy as np
from datetime import datetime

# Setup logging
logger = logging.getLogger("etl.clean")


def clean_html(raw_html: str) -> str:
    """Strips HTML tags from a string using regex."""
    if not isinstance(raw_html, str):
        return ""
    # Remove HTML tags
    clean_text = re.sub(r"<[^>]+>", " ", raw_html)
    # Normalize whitespaces
    clean_text = re.sub(r"\s+", " ", clean_text)
    return clean_text.strip()


def parse_salary_string(salary_str: str) -> tuple[float | None, float | None]:
    """
    Parses salary strings like '5-10 LPA' or '12 LPA' into numeric (min, max) floats.
    Assumes units in LPA.
    """
    if pd.isna(salary_str) or not isinstance(salary_str, str):
        return None, None
        
    # Clean string: lowercase, remove whitespace, remove 'lpa'
    s = salary_str.lower().replace("lpa", "").replace(",", "").strip()
    
    try:
        if "-" in s:
            parts = s.split("-")
            sal_min = float(parts[0].strip())
            sal_max = float(parts[1].strip())
            return sal_min, sal_max
        else:
            # Single value
            sal_val = float(s.strip())
            return sal_val, sal_val
    except ValueError:
        logger.warning(f"Could not parse salary string: '{salary_str}'")
        return None, None


def standardize_location(loc_str: str) -> str:
    """
    Standardizes location string by splitting on commas,
    removing country/state designations, stripping, and title casing.
    e.g., 'Sarasota, FL' -> 'Sarasota', 'Bangalore, India' -> 'Bangalore'
    """
    if pd.isna(loc_str) or not isinstance(loc_str, str):
        return "Unknown"
        
    parts = loc_str.split(",")
    main_loc = parts[0].strip()
    
    # Title-case normalization
    main_loc = main_loc.title()
    
    # Common mappings
    if main_loc == "Bengaluru":
        main_loc = "Bangalore"
    elif main_loc == "Delhi Ncr":
        main_loc = "Delhi NCR"
        
    return main_loc


def clean_muse_data(raw_jobs: list) -> pd.DataFrame:
    """
    Cleans raw Muse jobs list and converts to DataFrame.
    """
    logger.info("Cleaning Muse API job listings...")
    cleaned_records = []
    
    for job in raw_jobs:
        # Extract title and apply string operations
        title = job.get("name", "").strip().title()
        
        # Extract company
        company_dict = job.get("company", {})
        company_name = company_dict.get("name", "Unknown").strip().title()
        
        # Extract location
        locs = job.get("locations", [])
        loc_str = locs[0].get("name", "Unknown") if locs else "Unknown"
        location = standardize_location(loc_str)
        
        # Extract category
        cats = job.get("categories", [])
        category = cats[0].get("name", "Information Technology") if cats else "Information Technology"
        category = category.strip().title()
        
        # Extract publication date
        pub_date_str = job.get("publication_date")
        posted_date = None
        if pub_date_str:
            try:
                # Muse dates are in ISO format, e.g. 2025-01-17T00:02:34Z
                posted_date = datetime.strptime(pub_date_str.split(".")[0].replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
            except Exception:
                posted_date = datetime.utcnow()
                
        # Description
        desc_html = job.get("contents", "")
        description = clean_html(desc_html)
        
        # Muse listings usually do not have specific salary fields
        salary_min = None
        salary_max = None
        
        # Experience level mapping from Muse levels
        levels = job.get("levels", [])
        lvl_str = levels[0].get("name", "Not Specified") if levels else "Not Specified"
        lvl_str = lvl_str.strip().title()
        
        if "Entry" in lvl_str or "Intern" in lvl_str:
            experience_level = "Fresher"
        elif "Mid" in lvl_str:
            experience_level = "2-5 Years"
        elif "Senior" in lvl_str or "Lead" in lvl_str:
            experience_level = "5+ Years"
        else:
            experience_level = "0-2 Years"  # default middle ground
            
        # Employment type
        employment_type = "Full-Time"
        
        # Remote classification based on location
        remote_type = "Onsite"
        if "remote" in loc_str.lower() or "remote" in title.lower():
            remote_type = "Remote"
            
        cleaned_records.append({
            "title": title,
            "company_name": company_name,
            "location": location,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "experience_level": experience_level,
            "employment_type": employment_type,
            "industry": category,
            "remote_type": remote_type,
            "source": "The Muse",
            "posted_date": posted_date,
            "description": description,
            "skills_raw": "" # Skills extracted in transformation layer
        })
        
    df = pd.DataFrame(cleaned_records)
    logger.info(f"Cleaned {len(df)} Muse jobs.")
    return df


def clean_kaggle_data(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans raw Kaggle job listings DataFrame.
    """
    logger.info("Cleaning Kaggle historical job listings...")
    
    df = df_raw.copy()
    
    # 1. Apply drop_duplicates
    df = df.drop_duplicates()
    
    # 2. String cleaning (strip, lower, title)
    df["Job Title"] = df["Job Title"].fillna("Unknown").astype(str).str.strip().str.title()
    df["Company"] = df["Company"].fillna("Unknown").astype(str).str.strip().str.title()
    df["Industry"] = df["Industry"].fillna("Information Technology").astype(str).str.strip().str.title()
    df["Experience"] = df["Experience"].fillna("0-2 Years").astype(str).str.strip().str.title()
    df["Employment Type"] = df["Employment Type"].fillna("Full-Time").astype(str).str.strip().str.title()
    
    # Standardize Location
    df["Location"] = df["Location"].fillna("Unknown").astype(str).apply(standardize_location)
    
    # Parse salaries
    salaries = df["Salary"].apply(parse_salary_string)
    df["salary_min"] = [s[0] for s in salaries]
    df["salary_max"] = [s[1] for s in salaries]
    
    # Parse Date
    def parse_date(d_str):
        if pd.isna(d_str):
            return datetime.utcnow()
        try:
            return datetime.strptime(str(d_str), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            try:
                return datetime.strptime(str(d_str), "%Y-%m-%d")
            except ValueError:
                return datetime.utcnow()
                
    df["posted_date"] = df["Publication Date"].apply(parse_date)
    
    # Remote Type mapping based on Location
    def check_remote(row):
        loc = str(row["Location"]).lower()
        title = str(row["Job Title"]).lower()
        if "remote" in loc or "remote" in title:
            return "Remote"
        return "Onsite"  # Initial fallback; will refine in transformation
        
    df["remote_type"] = df.apply(check_remote, axis=1)
    
    # Select and rename columns to match standardized schema
    df_clean = pd.DataFrame({
        "title": df["Job Title"],
        "company_name": df["Company"],
        "location": df["Location"],
        "salary_min": df["salary_min"],
        "salary_max": df["salary_max"],
        "experience_level": df["Experience"],
        "employment_type": df["Employment Type"],
        "industry": df["Industry"],
        "remote_type": df["remote_type"],
        "source": "Kaggle",
        "posted_date": df["posted_date"],
        "description": df["Job Title"] + " " + df["Industry"], # Description substitute for skill parsing
        "skills_raw": df["Skills"].fillna("") # Raw skills column to extract from
    })
    
    logger.info(f"Cleaned {len(df_clean)} Kaggle jobs.")
    return df_clean


def merge_and_clean(raw_muse_jobs: list, raw_kaggle_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans both datasets and merges them into a single unified DataFrame.
    """
    df_muse = clean_muse_data(raw_muse_jobs)
    df_kaggle = clean_kaggle_data(raw_kaggle_df)
    
    # Concatenate
    merged_df = pd.concat([df_muse, df_kaggle], ignore_index=True)
    
    # Final duplicate check on title, company name, location, and source
    before_dup = len(merged_df)
    merged_df = merged_df.drop_duplicates(subset=["title", "company_name", "location", "source"])
    after_dup = len(merged_df)
    
    logger.info(f"Merged datasets. Removed {before_dup - after_dup} duplicate listings across sources. Total records: {after_dup}")
    return merged_df
