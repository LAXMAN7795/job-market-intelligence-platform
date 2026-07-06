import logging
import pandas as pd
from sqlalchemy.orm import Session
from database.postgres import Company, Job, Skill, JobSkill, db_session

# Setup logging
logger = logging.getLogger("etl.load")


def load_data_to_db(df: pd.DataFrame) -> None:
    """
    Loads clean, validated, and transformed DataFrame into PostgreSQL/SQLite via SQLAlchemy ORM.
    Ensures relational integrity and duplicate avoidance.
    """
    logger.info("Starting database loading operation...")
    session: Session = db_session()
    
    # 1. Pre-populate / Seed Skills table to make sure IDs exist
    predefined_skills = ["Python", "SQL", "Power BI", "Tableau", "Excel", "AWS", "Azure", "Spark", "Docker"]
    skill_map = {} # Maps skill name string -> Skill ORM object
    
    try:
        for skill_name in predefined_skills:
            # Query if skill exists, else create
            db_skill = session.query(Skill).filter(Skill.skill_name == skill_name).first()
            if not db_skill:
                db_skill = Skill(skill_name=skill_name)
                session.add(db_skill)
                session.flush() # Flush to populate ID
            skill_map[skill_name] = db_skill
            
        session.commit()
        logger.info("Skills master records initialized.")
    except Exception as e:
        session.rollback()
        logger.error(f"Error seeding skills: {e}")
        raise e

    # 2. Insert Companies and Jobs
    loaded_companies = 0
    loaded_jobs = 0
    loaded_job_skills = 0
    
    # Local cache to prevent redundant database queries for companies during loop execution
    company_cache = {}
    
    try:
        for _, row in df.iterrows():
            company_name = str(row["company_name"]).strip()
            industry = row["industry"]
            location = row["location"]
            
            # Resolve Company
            company_id = None
            if company_name in company_cache:
                company_id = company_cache[company_name]
            else:
                db_company = session.query(Company).filter(Company.company_name == company_name).first()
                if not db_company:
                    db_company = Company(
                        company_name=company_name,
                        industry=industry,
                        location=location
                    )
                    session.add(db_company)
                    session.flush()
                    loaded_companies += 1
                company_id = db_company.company_id
                company_cache[company_name] = company_id
                
            # Check for existing job entry (avoid duplicates)
            title = row["title"]
            source = row["source"]
            posted_date = row["posted_date"]
            
            db_job = session.query(Job).filter(
                Job.title == title,
                Job.company_id == company_id,
                Job.location == location,
                Job.source == source
            ).first()
            
            if db_job:
                # Job exists; skip or update. We will update attributes in case they changed
                db_job.salary_min = row["salary_min"]
                db_job.salary_max = row["salary_max"]
                db_job.experience_level = row["experience_level"]
                db_job.employment_type = row["employment_type"]
                db_job.industry = row["industry"]
                db_job.remote_type = row["remote_type"]
                db_job.posted_date = posted_date
                session.flush()
            else:
                # Create new Job record
                db_job = Job(
                    title=title,
                    company_id=company_id,
                    location=location,
                    salary_min=row["salary_min"],
                    salary_max=row["salary_max"],
                    experience_level=row["experience_level"],
                    employment_type=row["employment_type"],
                    industry=row["industry"],
                    remote_type=row["remote_type"],
                    source=source,
                    posted_date=posted_date
                )
                session.add(db_job)
                session.flush()
                loaded_jobs += 1
                
            # Resolve Job-Skill mappings (M2M)
            extracted_skills = row["extracted_skills"]
            if isinstance(extracted_skills, list):
                for skill_name in extracted_skills:
                    if skill_name in skill_map:
                        skill_obj = skill_map[skill_name]
                        
                        # Check if link exists
                        db_link = session.query(JobSkill).filter(
                            JobSkill.job_id == db_job.job_id,
                            JobSkill.skill_id == skill_obj.skill_id
                        ).first()
                        
                        if not db_link:
                            db_link = JobSkill(
                                job_id=db_job.job_id,
                                skill_id=skill_obj.skill_id
                            )
                            session.add(db_link)
                            loaded_job_skills += 1
                            
        # Final commit for the entire transaction batch
        session.commit()
        logger.info(f"Database loading finished successfully.")
        logger.info(f"Summary: New Companies={loaded_companies}, New Jobs={loaded_jobs}, Skill Links={loaded_job_skills}")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error loading jobs into database: {e}", exc_info=True)
        raise e
    finally:
        session.close()
        db_session.remove()
