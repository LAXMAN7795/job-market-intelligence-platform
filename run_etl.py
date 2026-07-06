import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Ensure the root directory is on the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Setup logging directory and file handler
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_file_path = os.path.join(LOG_DIR, "etl.log")

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file_path, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("etl_orchestrator")

# Import database initialization
from database.postgres import init_db

# Import Ingestion
from ingestion.muse_fetcher import fetch_muse_jobs, save_raw_jobs
from ingestion.kaggle_loader import load_kaggle_jobs

# Import ETL components
from etl.clean import merge_and_clean
from etl.validate import validate_data
from etl.transform import transform_data
from etl.load import load_data_to_db

# Import Reporting
from reports.market_report import generate_market_report


def run_pipeline() -> bool:
    """
    Orchestrates the entire data engineering pipeline:
    Database Init -> Ingest -> Clean -> Validate -> Transform -> Database Load -> Report.
    """
    logger.info("=========================================")
    logger.info("Starting Job Market Intelligence ETL Pipeline")
    logger.info("=========================================")
    
    start_time = datetime.now()
    
    try:
        # Step 1: Initialize Database Schema
        init_db()
        
        # Step 2: Data Ingestion
        logger.info("[Pipeline Step 1/5] Ingesting jobs from sources...")
        
        # Ingest Muse API
        muse_raw_jobs = fetch_muse_jobs()
        save_raw_jobs(muse_raw_jobs)
        
        # Ingest Kaggle historical dataset (auto-generates if not found)
        kaggle_raw_df = load_kaggle_jobs()
        
        # Step 3: Cleaning & Merging
        logger.info("[Pipeline Step 2/5] Cleaning and merging datasets...")
        merged_df = merge_and_clean(muse_raw_jobs, kaggle_raw_df)
        
        # Step 4: Quality Check / Validation
        logger.info("[Pipeline Step 3/5] Performing data validation checks...")
        validated_df, validation_report = validate_data(merged_df)
        logger.info(
            f"Validation Summary - Total: {validation_report['total_records_ingested']}, "
            f"Passed: {validation_report['records_passed']}, Failed: {validation_report['records_failed']}"
        )
        
        # Step 5: Feature Engineering & Transformation
        logger.info("[Pipeline Step 4/5] Executing transformation and skill extraction...")
        transformed_df = transform_data(validated_df)
        
        # Step 6: Database Loading
        logger.info("[Pipeline Step 5/5] Loading records into relational database...")
        load_data_to_db(transformed_df)
        
        # Step 7: Post-ETL Reporting
        logger.info("Pipeline successful. Generating Market Intelligence Report summary...")
        report_metrics = generate_market_report()
        logger.info(f"Report compiled. Most Demanded Skill: {report_metrics['top_skill']}, Top Hiring City: {report_metrics['top_city']}")
        
        duration = datetime.now() - start_time
        logger.info("=========================================")
        logger.info(f"ETL Pipeline Completed Successfully in {duration.total_seconds():.1f} seconds")
        logger.info("=========================================")
        return True
        
    except Exception as e:
        logger.critical(f"ETL Pipeline failed due to critical error: {e}", exc_info=True)
        logger.info("=========================================")
        logger.info("ETL Pipeline Terminated with Errors")
        logger.info("=========================================")
        return False


if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)
