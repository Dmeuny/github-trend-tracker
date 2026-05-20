import os
from dotenv import load_dotenv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DBT_DIR = r"C:\Users\dmeun\Desktop\Github API\my_project"
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))
RATE_LIMIT_FILE = os.path.join(SCRIPT_DIR, "last_run.json")

print("Looking for .env at:", os.path.join(SCRIPT_DIR, ".env"))
print("File exists:", os.path.exists(os.path.join(SCRIPT_DIR, ".env")))

import requests
import psycopg2
import hashlib
import json
import time
from datetime import datetime, timedelta
import base64
from prefect_dbt import PrefectDbtRunner, PrefectDbtSettings
from prefect import flow, task, get_run_logger

print("DB_HOST:", os.getenv("DB_HOST"))
print("DB_NAME:", os.getenv("DB_NAME"))

# -----------------------
# CONFIG
# -----------------------

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "github"),
    "user":     os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),
}

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# -----------------------
# CLASSIFICATION
# Priority: exclude → AI names → DE names → keyword match
# DE checked before AI — "airflow for LLMs" → DE
# -----------------------

def classify_repo(repo, readme_text=""):
    name     = repo["name"].lower()
    text     = (repo["name"] + " " + (repo["description"] or "")).lower()
    combined = text + " " + readme_text

    # Explicit exclusions — junk repos that match keywords accidentally
    exclude = ["c-plus-plus", "assemblies-of-putative"]
    if any(n in name for n in exclude):
        return "OTHER"

    # Explicit AI overrides — repos where name alone is enough
    ai_names = [
    "ollama", "dify", "mljar-supervised", "everything-claude-code",
    "firecrawl", "open-webui", "awesome-llm-apps", "hermes-agent",
    "langchain", "llama.cpp", "llm-course", "llms-from-scratch",
    "ml-for-beginners", "ragflow", "pathway", "llm-app",
    "llm-driven-data-engineering", "autogpt", "transformers",
    "funnlp", "mineru", "yt-channels-ds-ai-ml-cs"]
    if any(n in name for n in ai_names):
        return "AI"

    # Explicit DE overrides
    de_names = ["argo-workflows", "lightdash", "soda-core", "data-diff",
                "dolphinscheduler", "datafusion"]
    if any(n in name for n in de_names):
        return "DE"

    # Keyword matching on name + description + readme (top 20 repos only)
    if any(word in combined for word in [
        "data engineering", "dbt", "airflow", "spark", "etl", 
        "warehouse", "lakehouse", "ingestion", "kafka",
        "flink", "dagster", "prefect", "airbyte", "workflow",
        "orchestrat", "data quality", "fivetran"
    ]):
        return "DE"

    if any(word in combined for word in [
        "llm", "machine learning", "pytorch", "tensorflow",
        "transformer", "generative", "gpt", "gemini", "mistral",
        "inference", "fine-tun", "embedding", "vector", "rag",
        "diffusion", "automl", "neural", "deep learning"
    ]):
        return "AI"

    return "OTHER"


# -----------------------
# FINGERPRINT
# MD5 hash of all tracked fields.
# If anything changes → new SCD2 row.
# -----------------------

def make_fingerprint(repo, topic):
    payload = {
        "stars":       repo["stargazers_count"],
        "description": repo["description"],
        "language":    repo["language"],
        "topic":       topic,
    }
    return hashlib.md5(json.dumps(payload, sort_keys=True).encode()).hexdigest()


# -----------------------
# GITHUB FETCH
# Two broad OR queries replace five narrow ones.
# Deduplicates by repo ID across queries.
# -----------------------


def fetch_repos():

    print("🚨 RUNNING fetch_repos() 🚨")

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "data-engineering-project",
    }

    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    seen_ids = set()
    all_repos = []

    recent_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

    queries = [
        "data engineering",
        "dbt",
        "airflow",
        "machine learning",
        "LLM",
        "AI agents",
        "RAG",
        "langchain",
        "MCP server",
        "agentic AI",
    ]

    print("ACTIVE QUERIES:", queries)

    for query in queries:
        print(f"Fetching: '{query}'...")

        try:
            response = requests.get(
                "https://api.github.com/search/repositories",
                headers=headers,
                params={
                    "q": f"{query} pushed:>{recent_date} stars:>100",
                    "sort": "stars",
                    "order": "desc",
                    "per_page": 50,
                },
                timeout=10,
            )

            print(f"  Rate limit remaining: {response.headers.get('X-RateLimit-Remaining')}")

            if response.status_code == 403:
                print("  Rate limited. Sleeping 60s...")
                time.sleep(60)
                continue

            response.raise_for_status()

        except requests.exceptions.RequestException as e:
            print(f"  GitHub API error for query '{query}': {e}")
            continue

        for repo in response.json().get("items", []):
            if repo["id"] not in seen_ids:
                seen_ids.add(repo["id"])
                all_repos.append(repo)

        time.sleep(2)

    print(f"Total unique repos fetched: {len(all_repos)}")
    return all_repos

# -----------------------
# README FETCH
# Only enriches top 20 repos by stars to avoid rate limit issues.
# Improves classification accuracy for repos with sparse descriptions.
# -----------------------

def fetch_readme(owner, repo_name, headers):
    try:
        response = requests.get(
            f"https://api.github.com/repos/{owner}/{repo_name}/readme",
            headers=headers,
            timeout=10,
        )

        if response.status_code != 200:
            return ""

        content = response.json().get("content", "")
        return base64.b64decode(content).decode("utf-8", errors="ignore").lower()

    except Exception:
        return ""


# -----------------------
# STEP 1 — LOAD STAGING
# Wipe staging, then bulk insert fresh API data.
# Staging is a clean slate every run — it's not historical.
# -----------------------

def load_staging(cur, repos):
    print("\nTruncating staging_cleaned...")
    cur.execute("TRUNCATE TABLE staging_cleaned;")

    print("Loading staging_cleaned...")

    headers = {
        "Accept":     "application/vnd.github+json",
        "User-Agent": "data-engineering-project",
    }

    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    # Sort by stars so top 20 get README enrichment
    repos = sorted(repos, key=lambda x: x["stargazers_count"], reverse=True)

    for i, repo in enumerate(repos):
        readme_text = ""

        if i < 20:
            readme_text = fetch_readme(
                repo["owner"]["login"],
                repo["name"],
                headers
            )

        topic       = classify_repo(repo, readme_text)
        fingerprint = make_fingerprint(repo, topic)

        cur.execute("""
            INSERT INTO staging_cleaned (
                repo_id, name, description, language,
                stars, topic, fingerprint
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            str(repo["id"]),
            repo["name"],
            repo["description"],
            repo["language"],
            repo["stargazers_count"],
            topic,
            fingerprint,
        ))

    print(f"Staged {len(repos)} repos.")


# -----------------------
# STEP 2 — SCD TYPE 2 MERGE
# Set-based SQL — no Python loop, no row-by-row.
# Two queries replace what used to be hundreds of round trips.
# -----------------------

def run_scd2_merge(cur):
    print("\nRunning SCD Type 2 merge...")

    # Expire records where fingerprint changed
    cur.execute("""
        UPDATE repo_history rh
        SET    is_current = FALSE,
               end_date   = NOW()
        FROM   staging_cleaned s
        WHERE  rh.repo_id     = s.repo_id
        AND    rh.is_current  = TRUE
        AND    rh.fingerprint != s.fingerprint;
    """)
    print(f"  Expired rows: {cur.rowcount}")

    # Insert new current rows for changed or brand new repos
    cur.execute("""
        INSERT INTO repo_history (
            repo_id, name, description, language,
            stars, topic, fingerprint,
            start_date, end_date, is_current
        )
        SELECT
            s.repo_id,
            s.name,
            s.description,
            s.language,
            s.stars,
            s.topic,
            s.fingerprint,
            NOW(),
            NULL,
            TRUE
        FROM staging_cleaned s
        LEFT JOIN repo_history rh
            ON  rh.repo_id    = s.repo_id
            AND rh.is_current = TRUE
        WHERE rh.repo_id IS NULL
           OR rh.fingerprint != s.fingerprint;
    """)
    print(f"  Inserted rows: {cur.rowcount}")


# -----------------------
# MAIN
# Order of operations:
#   1. Fetch from GitHub API
#   2. TRUNCATE staging_cleaned
#   3. INSERT into staging_cleaned (with README enrichment for top 20)
#   4. UPDATE repo_history (expire changed)
#   5. INSERT into repo_history (new + changed)
#   6. Single commit
#   7. dbt snapshot
#   8. dbt run
# -----------------------

@flow(name="github-trend-pipeline")
def main():

    repos = fetch_repos()

    if not repos:
        print("No repos returned. Exiting without updating run timestamp.")
        return

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur  = conn.cursor()

        load_staging(cur, repos)
        run_scd2_merge(cur)

        conn.commit()
        print("\nAll changes committed.")

        cur.close()
        conn.close()

    except psycopg2.Error as e:
        print(f"Database error: {e}")
        return


    settings = PrefectDbtSettings(
        project_dir=DBT_DIR,
        profiles_dir=r"C:\Users\dmeun\.dbt"
    )
    runner = PrefectDbtRunner(settings=settings)
    runner.invoke(["snapshot"])
    runner.invoke(["run"])


if __name__ == "__main__":
    main.serve(
        name="github-daily",
        interval=43200,  # 12 hours
    )