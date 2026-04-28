select
    repo_id,
    name,

    -- DE score
    (
        3 * has_dbt +
        2 * has_pipeline +
        2 * has_orchestration +
        1 * has_sql
    ) as de_score,

    -- AI score
    (
        3 * has_llm +
        2 * has_ai_frameworks +
        2 * has_embeddings
    ) as ai_score

from {{ ref('repo_features') }}