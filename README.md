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
    |
Python + Prefect (Ingestion + Orchestration)
    |
Supabase / Postgres (Warehouse)
    |
dbt (Transformation + Classification)
    |
Streamlit Cloud (Dashboard)
```

This follows an **ELT pattern** -- raw data is loaded into the warehouse first, and all transformations happen inside the database via dbt.

---

## How It Works

### Ingestion (`ingest.py`)
- Fetches repositories from the GitHub Search API across multiple queries
- Deduplicates results by repo ID across queries
- Generates an MD5 fingerprint of key attributes (stars, description, language, topic) to detect meaningful changes
- Loads raw data into a `staging_cleaned` table -- truncated and reloaded on each run
- Automatically triggers `dbt snapshot` and `dbt run` after each successful ingest

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

### Classification (dbt)
Topic classification uses a weighted scoring system built across three dbt models:

**`repo_features`** -- extracts binary signals from repo name and description:
- DE signals: dbt, pipeline/ETL, orchestration (Airflow, Prefect, DAG), SQL/warehouse
- AI signals: LLM/GPT, AI frameworks (LangChain, Ollama, LLaMA), embeddings/RAG, ML frameworks

**`repo_scoring`** -- applies weighted scores to each signal:
- DE: dbt (3pts), pipeline/ETL (2pts), orchestration (2pts), SQL (1pt)
- AI: LLM/GPT (3pts), AI frameworks (2pts), embeddings (2pts), ML frameworks (2pts)

**`repo_classification`** -- makes the final DE / AI / OTHER decision:
- AI wins if `ai_score > de_score` and `ai_score >= 1`
- DE wins if `de_score > ai_score` and `de_score >= 2`
- Tied scores with `de_score >= 2` default to DE (DE keywords are noisier)
- Everything else is OTHER

### Transformation (dbt)
- `stg_github_repos` -- casts and cleans `staging_cleaned`
- `repo_history_snapshot` -- dbt snapshot implementing SCD2 using `check` strategy
- `repo_trends` -- mart model calculating day-over-day star growth and growth percentage per repo

### Dashboard (Streamlit)
- Connects directly to Supabase (hosted Postgres)
- Displays top repos by growth %, KPI metrics, and topic breakdown
- Filterable by topic (DE / AI / OTHER)
- Auto-refreshes data every hour via `st.cache_data(ttl=3600)`

---

## Schema

```sql
raw_github_repos    -- exact API dump (JSONB), never transformed
staging_cleaned     -- typed, fingerprinted -- truncated each run
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

## dbt DAG

```
stg_github_repos
    |-- repo_features
    |       |-- repo_scoring
    |               |-- repo_classification
    |-- repo_history_snapshot
            |-- repo_trends
```

---

## Stack

| Layer | Tool |
|-------|------|
| Ingestion | Python (requests, psycopg2) |
| Orchestration | Prefect |
| Warehouse | Supabase (hosted Postgres) |
| Transformation | dbt (postgres adapter) |
| Dashboard | Streamlit Cloud |
| Version Control | GitHub |

---

## Running This Project
The pipeline runs against Supabase in production. To run locally, you can use either Supabase or a local Postgres instance.

### Option A -- Cloud (Supabase)

1. Create a Supabase account
2. Create a new project and copy your connection string
3. Run `schema.sql` in the Supabase SQL Editor to create tables
4. Add credentials to `.env` (see below)
5. Point `profiles.yml` at your Supabase host with `sslmode: require`

### Option B -- Local Postgres

1. Install PostgreSQL locally
2. Create a database: `createdb github`
3. Run the schema: `psql -U postgres -d github -f schema.sql`

### Environment Variables

Create a `.env` file in the project root:

```
DB_HOST=your_host        # localhost or Supabase host
DB_PORT=5432
DB_NAME=postgres         # or github for local
DB_USER=postgres
DB_PASSWORD=yourpassword
GITHUB_TOKEN=ghp_yourtoken  # optional but recommended (raises API limit to 5000/hr)
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### dbt Setup

Update `~/.dbt/profiles.yml`:

```yaml
my_project:
  target: dev
  outputs:
    dev:
      type: postgres
      host: your_host
      port: 5432
      user: postgres
      password: yourpassword
      dbname: postgres
      schema: dbt
      threads: 4
      sslmode: require   # required for Supabase
```

### Run the Pipeline

```bash
# Run ingestion (automatically triggers dbt after)
python ingest.py

# Or run dbt manually
dbt snapshot
dbt run
```

### Launch the Dashboard

```bash
streamlit run app.py
```

### Streamlit Cloud Deployment

Add secrets in Streamlit Cloud -> Manage App -> Secrets:

```toml
DB_HOST = "your-supabase-pooler-host"
DB_PORT = "6543"
DB_NAME = "postgres"
DB_USER = "postgres.yourprojectid"
DB_PASSWORD = "yourpassword"
```

---

## Design Decisions

**Why SCD Type 2?**
Star counts change constantly. Overwriting records loses the history needed to answer "which repos grew the fastest this week?" SCD2 preserves every version so trend analysis is always possible.

**Why fingerprinting?**
Rather than comparing individual fields, an MD5 hash of all tracked attributes detects any change in a single comparison. If the fingerprint matches, nothing changed -- no update needed.

**Why ELT over ETL?**
Raw data lands in the warehouse first, untouched. If classification logic changes, the data can be reprocessed from the raw layer without hitting the API again. This is the idempotency principle -- same input, same output, always replayable.

**Why set-based SQL for the SCD2 merge?**
Two queries replace what was originally a Python loop making hundreds of individual database round trips. Set-based operations are faster, atomic, and easier to reason about at scale.

**Why a weighted scoring system for classification?**
Simple keyword matching gets to ~85% accuracy but struggles with repos that use adjacent terminology. A weighted scoring system separates signal strength -- "dbt" in a repo name is a stronger DE signal than "SQL" in a description. The multi-model dbt approach also keeps feature extraction, scoring, and classification as separate, testable layers.

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
[GitHub](https://github.com/Dmeuny) | [LinkedIn](https://www.linkedin.com/in/devin-meunier)
