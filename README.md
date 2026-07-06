# Job Market Intelligence Platform

A complete end-to-end Data Engineering and Analytics platform that aggregates, cleanses, validates, and analyzes job market data from free public sources. The platform transforms raw listings into actionable insights, persists them to a relational database, and renders interactive, HSL-tailored analytics dashboards suitable for portfolio display.

---

## Architecture Diagram

```mermaid
graph TD
    A[The Muse API] -->|JSON Ingestion| C[Raw Storage: data/raw/]
    B[Kaggle Dataset] -->|CSV Ingestion| C
    C --> D[ETL Pipeline: run_etl.py]
    D -->|Clean| E[clean.py]
    E -->|Validate| F[validate.py]
    F -->|Transform| G[transform.py]
    G -->|Load ORM| H[PostgreSQL / SQLite Warehouse]
    H --> I[Analytics Layer]
    I --> J[Streamlit Dashboard: app.py]
    I --> K[Automated Reporting: reports/market_report.py]
    K -->|Render md| J
```

---

## Project Structure

```
job-market-intelligence-platform/
├── app.py                      # Main Streamlit dashboard router
├── run_etl.py                  # Pipeline orchestrator
├── requirements.txt            # Project dependencies
├── .env                        # Local configurations
├── ingestion/                  # Ingestion scripts
│   ├── muse_fetcher.py         # The Muse API fetcher
│   └── kaggle_loader.py        # Kaggle dataset loader (with synthetic fallback)
├── etl/                        # Pipeline transformations
│   ├── clean.py                # Data cleaning / normalization
│   ├── validate.py             # Quality assurance and logging
│   ├── transform.py            # Feature bucketing and skill extraction
│   └── load.py                 # Relational DB loaders
├── database/                   # Schema and DB models
│   ├── postgres.py             # SQLAlchemy models & connection session
│   └── schema.sql              # Raw SQL DDL structure
├── analytics/                  # Analytical query modules
│   ├── hiring_analysis.py
│   ├── skill_analysis.py
│   ├── salary_analysis.py
│   └── geography_analysis.py
├── dashboard/                  # Streamlit dashboard pages
│   ├── executive_dashboard.py  # Page 1: Key performance indicators
│   ├── hiring_dashboard.py     # Page 2: Filterable hiring trends
│   ├── skill_dashboard.py      # Page 3: Technology and skill demand
│   ├── salary_dashboard.py     # Page 4: Salary ranges and boxes
│   └── geography_dashboard.py  # Page 5: City mappings & remote ratios
├── reports/                    # Intelligence summaries
│   └── market_report.py        # Report compiler (Page 6: Market Report)
├── data/                       # Local raw and processed datasets
│   ├── raw/
│   └── processed/
└── logs/                       # ETL run execution logs
```

---

## Features

1. **Ingestion & Loader Fallback**: Live fetches from The Muse API. Simulates Kaggle's historical data by generating 600+ highly realistic mock records containing salary, location, skills, and industry values if `data/raw/kaggle_jobs.csv` is not found.
2. **Quality Assurance**: Automated verification checking for mandatory fields, valid dates, logical salary bounds, and duplicate listings. Saves outputs to `data/processed/validation_report.json`.
3. **Feature Engineering**: Standardizes experiences and remote categories, extracts key technologies (Python, SQL, AWS, Azure, Power BI, etc.) from descriptions via regex boundaries, and places salaries into LPA buckets.
4. **Relational Schema**: Implements SQLAlchemy ORM mapping parent company listings, child jobs, and skills via a many-to-many lookup table.
5. **Interactive Filtering**: Streamlit UI filters dashboards dynamically (Location, Experience, Role, Industry) using database-level queries.
6. **Geographic Mapping**: Leverages local coordinates to plot job openings on an interactive scatter map.

---

## Setup & Local Installation

### Prerequisites
*   Python 3.12+ installed
*   PostgreSQL database (Optional: default fallback uses a local SQLite database for instant running)

### Step 1: Clone & Initialize Environment
Clone or navigate to the workspace, create your virtual environment, and install dependencies:

```bash
# Set up virtual environment
python -m venv venv
venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables
Copy `.env.example` to `.env`:

```bash
copy .env.example .env
```

To configure **PostgreSQL** (e.g. Neon PostgreSQL), edit `.env` and configure `DATABASE_URL`:
```ini
DATABASE_URL=postgresql://username:password@your-neon-host.neon.tech/neondb?sslmode=require
```
Otherwise, leave the default `sqlite:///data/job_market.db` to run the project locally without setting up database servers.

---

## Running the Platform

### Run the ETL Pipeline
This script runs the ingestion, processes the datasets, creates the database tables, inserts the records, and creates the report:

```bash
python run_etl.py
```
Check `logs/etl.log` to view step execution logs, and `data/processed/validation_report.json` for data quality stats.

### Run the Streamlit Dashboard
Launch the dashboard locally:

```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Production Deployment

### Database (Neon PostgreSQL)
1. Register for a free account at [Neon.tech](https://neon.tech/).
2. Create a new project and copy your database Connection String.
3. Replace the `DATABASE_URL` in your Streamlit environment variables with this string.

### Dashboard (Streamlit Cloud)
1. Push your repository to GitHub.
2. Log into [Streamlit Community Cloud](https://share.streamlit.io/).
3. Click "New App", select your GitHub repository, branch, and `app.py` as the entrypoint.
4. Under **Advanced Settings**, paste the contents of your `.env` file (namely `DATABASE_URL=...`) into the **Secrets** textbox.
5. Deploy. Streamlit will install packages from `requirements.txt` and connect directly to your database.
