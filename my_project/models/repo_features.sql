with base as (

    select
        repo_id,
        name,
        description,
        language,
        topic,

        regexp_replace(
            lower(
                coalesce(name, '') || ' ' ||
                coalesce(description, '') || ' ' ||
                coalesce(topic, '')
            ),
            '[^a-z0-9]+',
            ' ',
            'g'
        ) as search_text

    from {{ ref('stg_github_repos') }}

),

features as (

    select
        repo_id,
        name,
        description,
        language,
        topic,

        -- ============================================================
        -- DATA ENGINEERING
        -- ============================================================

        case
            when search_text like '%dbt%'
            then 1 else 0
        end as has_dbt,

        case
    when search_text like '%data engineering%'
        or search_text like '%data engineer%'
        or search_text like '%etl%'
        or search_text like '%elt%'
        or search_text like '%data pipeline%'
        or search_text like '%data pipelines%'
        or search_text like '%data ingestion%'
        or search_text like '%data integration%'
        or search_text like '%data quality%'
        or search_text like '%data contract%'
        or search_text like '%data contracts%'
        or search_text like '%data validation%'
        or search_text like '%data observability%'
    then 1 else 0
end as has_data_pipeline,

        case
            when search_text like '%airflow%'
                or search_text like '%dagster%'
                or search_text like '%prefect%'
                or search_text like '%orchestration%'
                or search_text like '%workflow engine%'
                or search_text like '%workflow orchestration%'
            then 1 else 0
        end as has_orchestration,

        case
            when search_text like '%snowflake%'
                or search_text like '%bigquery%'
                or search_text like '%redshift%'
                or search_text like '%databricks%'
                or search_text like '%lakehouse%'
                or search_text like '%data warehouse%'
                or search_text like '%data lake%'
                or search_text like '%data platform%'
            then 1 else 0
        end as has_data_platform,

        case
            when search_text like '%dimensional model%'
                or search_text like '%data model%'
                or search_text like '%data modeling%'
                or search_text like '%data modelling%'
                or search_text like '%star schema%'
                or search_text like '%slowly changing dimension%'
                or search_text like '%semantic layer%'
            then 1 else 0
        end as has_data_modeling,

        case
            when search_text like '%spark%'
                or search_text like '%apache spark%'
                or search_text like '%flink%'
                or search_text like '%apache flink%'
                or search_text like '%kafka%'
                or search_text like '%apache kafka%'
                or search_text like '%stream processing%'
                or search_text like '%distributed processing%'
            then 1 else 0
        end as has_data_processing,

        -- ============================================================
        -- AI / MACHINE LEARNING
        -- ============================================================

        case
    when search_text like '%llm%'
        or search_text like '%large language model%'
        or search_text like '%generative ai%'
        or search_text like '%artificial intelligence%'
        or search_text like '%ai engineering%'
        or search_text like '%ai engineer%'
        or search_text like '%ai driven%'
        or search_text like '%ai driven development%'
        or search_text like '%conversational ai%'
        or search_text like '%openai%'
        or search_text like '%gpt%'
        or search_text like '% ai %'
        or search_text like '%ai application%'
        or search_text like '%ai applications%'
        or search_text like '%ai powered%'
        or search_text like '%ai powered application%'
        or search_text like '%ai coding%'
        or search_text like '%coding assistant%'
        or search_text like '%ai assistant%'
        or topic = 'AI'
    then 1 else 0
end as has_llm,
        case
            when search_text like '%langchain%'
                or search_text like '%ollama%'
                or search_text like '%huggingface%'
                or search_text like '%hugging face%'
                or search_text like '%claude%'
                or search_text like '%anthropic%'
                or search_text like '%gemini%'
                or search_text like '%llama%'
                or search_text like '%transformer%'
                or search_text like '%transformers%'
                or search_text like '%vllm%'
                or search_text like '%litellm%'
            then 1 else 0
        end as has_ai_frameworks,

        case
            when search_text like '%rag%'
                or search_text like '%retrieval augmented%'
                or search_text like '%retrieval augmented generation%'
                or search_text like '%embedding%'
                or search_text like '%embeddings%'
                or search_text like '%vector database%'
                or search_text like '%vector store%'
                or search_text like '%vector search%'
                or search_text like '%semantic search%'
            then 1 else 0
        end as has_retrieval,

        case
            when search_text like '%machine learning%'
                or search_text like '%deep learning%'
                or search_text like '%neural network%'
                or search_text like '%neural networks%'
                or search_text like '%pytorch%'
                or search_text like '%tensorflow%'
                or search_text like '%scikit learn%'
                or search_text like '%xgboost%'
                or search_text like '%inference%'
                or search_text like '%mlops%'
                or search_text like '%computer vision%'
                or search_text like '%reinforcement learning%'
                or search_text like '%fine tuning%'
            then 1 else 0
        end as has_ml,

        case
            when search_text like '%agent%'
                or search_text like '%agents%'
                or search_text like '%agentic%'
                or search_text like '%coding agent%'
                or search_text like '%coding agents%'
                or search_text like '%ai assistant%'
                or search_text like '%ai assistants%'
                or search_text like '%ai powered%'
                or search_text like '%autonomous agent%'
                or search_text like '%autonomous agents%'
                or search_text like '%mcp%'
                or search_text like '%model context protocol%'
                or search_text like '%tool calling%'
                or search_text like '%function calling%'
            then 1 else 0
        end as has_agents

    from base

)

select *
from features