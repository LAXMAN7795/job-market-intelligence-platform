import os
import json
import logging
import time
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("muse_fetcher")

# API Configuration
MUSE_API_URL = "https://www.themuse.com/api/public/jobs"
RAW_DATA_DIR = os.path.join("data", "raw")
DEFAULT_PAGES = int(os.getenv("MUSE_API_PAGES", "5"))


def fetch_muse_jobs(pages: int = DEFAULT_PAGES) -> list:
    """
    Fetches job listings from The Muse API across multiple pages.
    
    Args:
        pages (int): The number of pages to retrieve.
        
    Returns:
        list: A list of job listings (dictionaries).
    """
    logger.info(f"Starting Muse API ingestion. Targeted pages: {pages}")
    all_jobs = []
    
    for page in range(1, pages + 1):
        params = {"page": page}
        logger.info(f"Fetching page {page} of {pages} from The Muse API...")
        
        try:
            # Send request
            response = requests.get(MUSE_API_URL, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                logger.warning(f"No results found on page {page}. Terminating fetch.")
                break
                
            all_jobs.extend(results)
            logger.info(f"Successfully fetched {len(results)} jobs from page {page}.")
            
            # Simple rate limiting protection
            time.sleep(1.0)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching page {page} from Muse API: {e}")
            # Continue to next page rather than crashing, or stop depending on criticality
            break
            
    logger.info(f"Muse Ingestion completed. Total jobs retrieved: {len(all_jobs)}")
    return all_jobs


def save_raw_jobs(jobs: list, filename: str = "muse_jobs.json") -> str:
    """
    Saves raw list of jobs to a JSON file in data/raw/.
    
    Args:
        jobs (list): The list of job dictionaries.
        filename (str): Target filename.
        
    Returns:
        str: Absolute path of the saved file.
    """
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    filepath = os.path.join(RAW_DATA_DIR, filename)
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(jobs, f, indent=4, ensure_ascii=False)
        logger.info(f"Successfully saved raw Muse jobs to {filepath}")
    except Exception as e:
        logger.error(f"Failed to save raw Muse jobs: {e}", exc_info=True)
        raise e
        
    return filepath


if __name__ == "__main__":
    jobs = fetch_muse_jobs()
    save_raw_jobs(jobs)
