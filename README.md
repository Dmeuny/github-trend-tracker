# GitHub Trend Tracker

A fully automated ELT pipeline that tracks momentum across Data Engineering and AI GitHub repositories — built with Python, Postgres, dbt, Prefect, and Streamlit.

**Live Dashboard → [repo-trend-tracker-rkwrfwtffgcrs3gegd2gpy.streamlit.app](https://repo-trend-tracker-rkwrfwtffgcrs3gegd2gpy.streamlit.app)**

---

## What It Does

Most data pipelines overwrite records. When something changes, the previous state is gone.

This pipeline preserves history — so you can ask "what did this repo look like 3 months ago?" and actually get an answer. It pulls repositories from the GitHub API across multiple search queries, classifies them by topic, and tracks how they change over time: stars, descriptions, language, and topic.

---

## Architecture

```
GitHub API (Source)
    ↓
Python + Prefect (Ingestion + Orchestration)
    ↓
Supabase / Postgres (Warehouse)
    ↓
dbt (Transformation)
    ↓
Streamlit Cloud (Dashboard)
```

This follows an **ELT pattern** — raw data is loaded into the warehouse first, and transformations happen inside the database via dbt.

---

## How It Works

### Ingestion (`ingest.py`)
- Fetches repositories from the GitHub Search API across multiple queries
- Deduplicates results by repo ID across queries
- Classifies each repo as `DE`, `AI`, or `OTHER` using keyword matching on name, description, and README (top 20 repos)
- Generates an MD5 fingerprint of key attributes (stars, description, language, topic) to detect meaningful changes
- Loads raw data into a `staging_cleaned` table — truncated and reloaded on each run

### Change Detection (SCD Type 2)
- Compares fingerprints between staging and history
- If a change is detected: expires the old record (`is_current = FALSE`) and inserts a new current row
- Two set-based SQL queries replace what would otherwise be hundreds of row-by-row round trips
- Every version of every repo is preserved with `start_date` and `end_date` timestamps

### Orchestration (Prefect)
- `ingest.py` is wrapped as a Prefect `@flow`
- Scheduled to run daily via `main.serve()` with a 24-hour interval
- Flow runs are tracked and visible in the Prefect UI
- A rate limit guard (`last_run.json`) prevents duplicate runs within the interval

### Transformation (dbt)
- `stg_github_repos` — staging model that casts and cleans `staging_cleaned`
- `repo_history_snapshot` — dbt snapshot implementing SCD2 natively using `check` strategy on stars, description, language, and topic
- `repo_trends` — mart model calculating day-over-day star growth and growth percentage per repo

### Dashboard (Streamlit)
- Connects directly to Supabase (hosted Postgres)
- Displays top repos by growth %, KPI metrics, and topic breakdown
- Filterable by topic (DE / AI / OTHER)
- Auto-refreshes data every hour via `st.cache_data(ttl=3600)`

---

## Schema

```sql
raw_github_repos    -- exact API dump (JSONB), never transformed
staging_cleaned     -- typed, classified, fingerprinted — truncated each run
repo_history        -- SCD Type 2 history table, one row per version per repo
```

**Key columns in `repo_history`:**

| Column | Description |
|--------|-------------|
| `repo_id` | GitHub repo ID |
| `name` | Repository name |
| `stars` | Star count at this version |
| `topic` | DE / AI / OTHER |
| `fingerprint` | MD5 hash of tracked fields |
| `start_date` | When this version became current |
| `end_date` | When this version was replaced (NULL if current) |
| `is_current` | TRUE for the live record |

---

## Stack

| Layer | Tool |
|-------|------|
| Ingestion | Python (requests, psycopg2) |
| Orchestration | Prefect |
| Warehouse | Supabase (Postgres) |
| Transformation | dbt (postgres adapter) |
| Dashboard | Streamlit Cloud |
| Version Control | GitHub |

---

## Local Setup

**1. Clone the repo**
```bash
git clone https://github.com/Dmeuny/github-trend-tracker.git
cd github-trend-tracker
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Create a `.env` file**
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=github
DB_USER=postgres
DB_PASSWORD=yourpassword
GITHUB_TOKEN=ghp_yourtoken
```

**4. Create the schema**
```bash
psql -U postgres -d github -f schema.sql
```

**5. Run the pipeline**
```bash
python ingest.py
dbt snapshot
dbt run
```

**6. Launch the dashboard**
```bash
streamlit run app.py
```

---

## Design Decisions

**Why SCD Type 2?**
Star counts change constantly. Overwriting records loses the history needed to answer "which repos grew the fastest this week?" SCD2 preserves every version so trend analysis is always possible.

**Why fingerprinting?**
Rather than comparing individual fields, an MD5 hash of all tracked attributes detects any change in a single comparison. If the fingerprint matches, nothing changed — no update needed.

**Why ELT over ETL?**
Raw data lands in the warehouse first, untouched. If classification logic changes, the data can be reprocessed from the raw layer without hitting the API again. This is the idempotency principle — same input, same output, always replayable.

**Why set-based SQL for the SCD2 merge?**
Two queries replace what was originally a Python loop making hundreds of individual database round trips. Set-based operations are faster, atomic, and easier to reason about at scale.

---

## Roadmap

- [ ] Migrate to Snowflake for cloud warehouse experience
- [ ] Add Airflow DAG as alternative orchestration layer
- [ ] Expand classification with ML-based topic detection
- [ ] Add keyword frequency trending (which terms appear most in rising repos)
- [ ] Connect Tableau dashboard for additional visualization layer

---

## Author

**Devin Meunier**
[GitHub](https://github.com/Dmeuny) · [LinkedIn](https://www.linkedin.com/in/devin-meunier)
