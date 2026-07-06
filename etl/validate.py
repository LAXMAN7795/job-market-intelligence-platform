import os
import json
import logging
import pandas as pd
from datetime import datetime

# Setup logging
logger = logging.getLogger("etl.validate")

PROCESSED_DATA_DIR = os.path.join("data", "processed")


def validate_data(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Validates job listings DataFrame against predefined checks:
    - Required fields (title, company_name, source)
    - Salary validation (min <= max, positive)
    - Date format (valid, non-future dates)
    - Duplicates
    
    Generates a validation summary report and returns the cleaned, validated DataFrame.
    """
    logger.info("Starting data validation checks...")
    total_records = len(df)
    
    # Reports dictionary structure
    report = {
        "validation_timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "total_records_ingested": total_records,
        "failures": {
            "missing_required_fields": 0,
            "invalid_salaries": 0,
            "invalid_dates": 0,
            "duplicate_records": 0
        },
        "records_passed": 0,
        "records_failed": 0
    }
    
    # Trace indices of records to drop
    indices_to_drop = set()
    
    for idx, row in df.iterrows():
        # 1. Required Fields Check
        if pd.isna(row.get("title")) or not str(row.get("title")).strip() or \
           pd.isna(row.get("company_name")) or not str(row.get("company_name")).strip() or \
           pd.isna(row.get("source")) or not str(row.get("source")).strip():
            indices_to_drop.add(idx)
            report["failures"]["missing_required_fields"] += 1
            continue
            
        # 2. Salary Values Check (only if salary is populated)
        sal_min = row.get("salary_min")
        sal_max = row.get("salary_max")
        
        if pd.notna(sal_min) and pd.notna(sal_max):
            # Check for negative salaries or min > max
            if sal_min < 0 or sal_max < 0 or sal_min > sal_max:
                indices_to_drop.add(idx)
                report["failures"]["invalid_salaries"] += 1
                continue
                
        # 3. Date Check
        posted_date = row.get("posted_date")
        if pd.isna(posted_date) or not isinstance(posted_date, datetime):
            indices_to_drop.add(idx)
            report["failures"]["invalid_dates"] += 1
            continue
        elif posted_date > datetime.utcnow():
            # Future publication date is invalid
            indices_to_drop.add(idx)
            report["failures"]["invalid_dates"] += 1
            continue
            
    # 4. Duplicate Check
    # (Since we ran drop_duplicates in clean.py, we evaluate duplicates remaining)
    duplicate_mask = df.duplicated(subset=["title", "company_name", "location", "source"])
    duplicate_count = duplicate_mask.sum()
    report["failures"]["duplicate_records"] = int(duplicate_count)
    
    # Filter the DataFrame
    valid_df = df.drop(index=list(indices_to_drop)).copy()
    
    # Compile final metrics
    report["records_failed"] = len(indices_to_drop)
    report["records_passed"] = len(valid_df)
    
    logger.info(f"Validation completed. Passed: {report['records_passed']}, Failed: {report['records_failed']}")
    
    # Save the report
    save_validation_report(report)
    
    return valid_df, report


def save_validation_report(report: dict, filename: str = "validation_report.json") -> None:
    """Saves the validation report as a JSON file in data/processed/."""
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    filepath = os.path.join(PROCESSED_DATA_DIR, filename)
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4)
        logger.info(f"Validation report saved to {filepath}")
    except Exception as e:
        logger.error(f"Failed to save validation report: {e}", exc_info=True)
        raise e
