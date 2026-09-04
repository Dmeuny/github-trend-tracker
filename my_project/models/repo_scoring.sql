select
    repo_id,
    name,

    -- DE score
    (
        4 * has_dbt +
        4 * has_data_pipeline +
        3 * has_orchestration +
        3 * has_data_platform +
        3 * has_data_modeling +
        2 * has_data_processing
    ) as de_score,

    -- AI score
    (
        4 * has_llm +
        3 * has_ai_frameworks +
        3 * has_retrieval +
        3 * has_ml +
        4 * has_agents
    ) as ai_score

from {{ ref('repo_features') }}