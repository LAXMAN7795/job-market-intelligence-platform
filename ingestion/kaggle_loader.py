import os
import random
import logging
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logger = logging.getLogger("kaggle_loader")

RAW_DATA_DIR = os.path.join("data", "raw")
KAGGLE_CSV_NAME = "kaggle_jobs.csv"
KAGGLE_FILE_PATH = os.path.join(RAW_DATA_DIR, KAGGLE_CSV_NAME)


def generate_synthetic_kaggle_data(filepath: str, num_records: int = 600) -> None:
    """
    Generates a rich, realistic synthetic historical job dataset in CSV format
    to simulate Kaggle dataset when not present.
    """
    logger.info(f"Target Kaggle CSV not found. Generating {num_records} synthetic job records...")
    
    # Pre-defined pools for random selection
    companies = [
        "Tech Mahindra", "Infosys", "Wipro", "Tata Consultancy Services", "HCLTech",
        "Cognizant", "Accenture", "Amazon", "Google India", "Microsoft India",
        "Flipkart", "Paytm", "PhonePe", "CRED", "Reliance Jio", "Airtel",
        "ICICI Bank", "HDFC Bank", "Deloitte", "KPMG", "EY", "PwC"
    ]
    
    roles = [
        "Data Engineer", "Senior Data Engineer", "Data Analyst", "Business Analyst",
        "Data Scientist", "Machine Learning Engineer", "Python Developer",
        "BI Developer", "Database Administrator", "Cloud Architect",
        "DevOps Engineer", "Software Engineer", "Full Stack Developer"
    ]
    
    cities = ["Bangalore", "Mumbai", "Hyderabad", "Pune", "Chennai", "Delhi NCR", "Noida", "Gurgaon"]
    
    industries = [
        "Information Technology", "Finance & Banking", "Healthcare", 
        "E-commerce", "Telecommunications", "Consulting", "Retail"
    ]
    
    experience_levels = ["Fresher", "0-2 Years", "2-5 Years", "5+ Years"]
    employment_types = ["Full-time", "Part-time", "Contract", "Internship"]
    
    # Skill sets corresponding to roles
    role_skills_map = {
        "Data Engineer": ["Python", "SQL", "Spark", "AWS", "Docker"],
        "Senior Data Engineer": ["Python", "SQL", "Spark", "AWS", "Azure", "Docker"],
        "Data Analyst": ["SQL", "Excel", "Tableau", "Power BI"],
        "Business Analyst": ["Excel", "Power BI", "Tableau", "SQL"],
        "Data Scientist": ["Python", "SQL", "Spark", "AWS"],
        "Machine Learning Engineer": ["Python", "Spark", "Docker", "AWS"],
        "Python Developer": ["Python", "SQL", "Docker", "AWS"],
        "BI Developer": ["Power BI", "Tableau", "SQL", "Excel"],
        "Database Administrator": ["SQL", "Azure", "Excel"],
        "Cloud Architect": ["AWS", "Azure", "Docker"],
        "DevOps Engineer": ["Docker", "AWS", "Azure", "Python"],
        "Software Engineer": ["Python", "SQL", "Docker"],
        "Full Stack Developer": ["Python", "SQL", "Docker", "Azure"]
    }
    
    # Base skills list
    all_skills = ["Python", "SQL", "Power BI", "Tableau", "Excel", "AWS", "Azure", "Spark", "Docker"]
    
    data = []
    start_date = datetime.now() - timedelta(days=90)
    
    for i in range(num_records):
        role = random.choice(roles)
        company = random.choice(companies)
        industry = random.choice(industries)
        experience = random.choice(experience_levels)
        employment_type = random.choice(employment_types)
        
        # Decide location and remote type
        loc_choice = random.choice(cities + ["Remote"])
        if loc_choice == "Remote":
            location = random.choice(cities)
            remote_type = "Remote"
        else:
            location = loc_choice
            remote_type = random.choice(["Onsite", "Hybrid", "Remote"])
            
        # Determine Salary in LPA based on role and experience
        if experience == "Fresher":
            base_min, base_max = 2.5, 4.5
        elif experience == "0-2 Years":
            base_min, base_max = 4.0, 7.5
        elif experience == "2-5 Years":
            base_min, base_max = 7.0, 14.0
        else: # 5+ Years
            base_min, base_max = 13.0, 35.0
            
        # Add factor based on role complexity
        role_factor = 1.0
        if "Senior" in role or "Architect" in role:
            role_factor = 1.4
        elif "Analyst" in role:
            role_factor = 0.8
            
        salary_min = round(base_min * role_factor, 1)
        salary_max = round(base_max * role_factor, 1)
        
        # Extract base skills for role, inject a bit of noise
        core_skills = role_skills_map.get(role, ["Python"])
        sampled_skills = list(set(core_skills + random.choices(all_skills, k=random.randint(1, 3))))
        # Skill column string format (comma separated)
        skills_str = ", ".join(sampled_skills)
        
        # Random publication date in last 90 days
        post_date = start_date + timedelta(
            days=random.randint(0, 90),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )
        
        data.append({
            "Job Title": role,
            "Company": company,
            "Location": f"{location}, India" if remote_type != "Remote" else "Remote, India",
            "Salary": f"{salary_min}-{salary_max} LPA" if random.random() > 0.1 else f"{salary_max} LPA",
            "Skills": skills_str,
            "Industry": industry,
            "Experience": experience,
            "Employment Type": employment_type,
            "Publication Date": post_date.strftime("%Y-%m-%d %H:%M:%S")
        })
        
    df = pd.DataFrame(data)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False, encoding="utf-8")
    logger.info(f"Synthetic Kaggle dataset successfully created and saved to {filepath}")


def load_kaggle_jobs() -> pd.DataFrame:
    """
    Loads Kaggle jobs from local CSV.
    Generates synthetic file if it is not found.
    
    Returns:
        pd.DataFrame: Loaded Kaggle jobs.
    """
    if not os.path.exists(KAGGLE_FILE_PATH):
        generate_synthetic_kaggle_data(KAGGLE_FILE_PATH)
        
    logger.info(f"Loading Kaggle jobs from {KAGGLE_FILE_PATH}...")
    try:
        df = pd.read_csv(KAGGLE_FILE_PATH, encoding="utf-8")
        logger.info(f"Successfully loaded {len(df)} records from Kaggle CSV.")
        return df
    except Exception as e:
        logger.error(f"Failed to load Kaggle CSV: {e}", exc_info=True)
        raise e


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    df = load_kaggle_jobs()
    print(df.head())
