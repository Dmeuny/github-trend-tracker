select
    repo_id,
    name,
    description,
    language,
    topic,

    -- DE signals
-- DE signals
    case when lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%dbt%' then 1 else 0 end as has_dbt,

    case when lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%pipeline%' 
        or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%etl%' 
        or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%elt%' 
        or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%ingestion%'
        or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%data engineering%'
        or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%data engineer%' 
        or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%orchestration%'
        or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%data stack%'
        or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%data quality%'
        or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%warehousing%'
        or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%analytics database%'
        or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%workflow engine%'
        or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%business intelligence%'
        or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%compare tables%'
        or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%data stack%'
        or lower(name) like '%data-engineering%'
        or lower(name) like '%data engineering%'
    then 1 else 0 end as has_pipeline,

    case when lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%airflow%' 
        or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%prefect%' 
        or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%dag%' 
    then 1 else 0 end as has_orchestration,

    case when language = 'SQL' 
        or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%spark%' 
        or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%bigquery%' 
        or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%warehouse%' 
    then 1 else 0 end as has_sql,

    -- AI signals
    -- AI signals
    case when lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%llm%' 
          or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%gpt%' 
          or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%transformer%' 
    then 1 else 0 end as has_llm,

    case when lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%langchain%' 
        or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%llama%' 
        or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%huggingface%' 
        or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%autogpt%' 
        or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%ollama%' 
        or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%webui%' 
        or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%agent%'
        or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%claude%'
        or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%codex%'
    then 1 else 0 end as has_ai_frameworks,

    case when lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%embedding%' 
           or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%vector%' 
           or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%rag%' 
    then 1 else 0 end as has_embeddings,

    case when lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%machine learning%' 
      or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%deep learning%'
      or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%neural%'
      or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%tensorflow%'
      or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%pytorch%'
      or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%scikit%'
      or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%automl%'
      or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%mlops%'
      or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%ai-driven%'
      or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%scrape%'
      or lower(coalesce(name,'') || ' ' || coalesce(description,'')) like '%jupyterlab%'
    then 1 else 0 end as has_ml_framework

from {{ ref('stg_github_repos') }}