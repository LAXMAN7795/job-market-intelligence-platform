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
    skill_map = {} # Maps skill name string (lowercase) -> Skill ORM object
    
    try:
        # Load all existing skills to memory case-insensitively
        existing_skills = {s.skill_name.lower().strip(): s for s in session.query(Skill).all()}
        for skill_name in predefined_skills:
            skill_key = skill_name.lower().strip()
            if skill_key in existing_skills:
                skill_map[skill_key] = existing_skills[skill_key]
            else:
                db_skill = Skill(skill_name=skill_name)
                session.add(db_skill)
                session.flush() # Flush to populate ID
                skill_map[skill_key] = db_skill
                existing_skills[skill_key] = db_skill
            
        session.commit()
        logger.info("Skills master records initialized.")
    except Exception as e:
        session.rollback()
        logger.error(f"Error seeding skills: {e}")
        raise e

    # 2. Pre-fetch Companies, Jobs, and Links into memory to avoid network round-trips (case-insensitively)
    try:
        logger.info("Pre-fetching database indexes into memory caches...")
        # Load existing companies case-insensitively
        company_cache = {c.company_name.lower().strip(): c.company_id for c in session.query(Company).all()}
        
        # Load existing jobs case-insensitively (unique compound key: title, company_id, location, source)
        job_cache = {}
        for j in session.query(Job).all():
            key = (j.title.lower().strip(), j.company_id, (j.location or "").lower().strip(), j.source.lower().strip())
            job_cache[key] = j
            
        # Load existing Job-Skill links
        job_skill_links = {(js.job_id, js.skill_id) for js in session.query(JobSkill).all()}
        
        loaded_companies = 0
        loaded_jobs = 0
        loaded_job_skills = 0
        
        logger.info("Starting batch processing loop...")
        for _, row in df.iterrows():
            company_name = str(row["company_name"]).strip()
            industry = row["industry"]
            location = row["location"]
            
            # Resolve Company (case-insensitively)
            company_id = None
            company_key = company_name.lower().strip()
            if company_key in company_cache:
                company_id = company_cache[company_key]
            else:
                db_company = Company(
                    company_name=company_name,
                    industry=industry,
                    location=location
                )
                session.add(db_company)
                session.flush()
                company_id = db_company.company_id
                company_cache[company_key] = company_id
                loaded_companies += 1
                
            # Check for existing job entry (case-insensitively)
            title = row["title"]
            source = row["source"]
            posted_date = row["posted_date"]
            
            job_key = (title.lower().strip(), company_id, (location or "").lower().strip(), source.lower().strip())
            
            db_job = None
            if job_key in job_cache:
                db_job = job_cache[job_key]
                # Update attributes
                db_job.salary_min = row["salary_min"]
                db_job.salary_max = row["salary_max"]
                db_job.experience_level = row["experience_level"]
                db_job.employment_type = row["employment_type"]
                db_job.industry = row["industry"]
                db_job.remote_type = row["remote_type"]
                db_job.posted_date = posted_date
                session.flush()
            else:
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
                job_cache[job_key] = db_job
                loaded_jobs += 1
                
            # Resolve Job-Skill links
            extracted_skills = row["extracted_skills"]
            if isinstance(extracted_skills, list):
                for skill_name in extracted_skills:
                    skill_key = skill_name.lower().strip()
                    if skill_key in skill_map:
                        skill_obj = skill_map[skill_key]
                        link_key = (db_job.job_id, skill_obj.skill_id)
                        
                        if link_key not in job_skill_links:
                            db_link = JobSkill(
                                job_id=db_job.job_id,
                                skill_id=skill_obj.skill_id
                            )
                            session.add(db_link)
                            job_skill_links.add(link_key)
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
