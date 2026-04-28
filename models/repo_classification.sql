{{ config(
    materialized='view'
) }}

select
    repo_id,
    name,
    de_score,
    ai_score,

CASE
    WHEN ai_score > de_score AND ai_score >= 1 THEN 'AI'
    WHEN de_score > ai_score AND de_score >= 2 THEN 'DE'
    WHEN de_score = ai_score AND de_score >= 2 THEN 'DE'  -- tiebreaker favors DE
    ELSE 'OTHER'
END as topic_reclassified

from {{ ref('repo_scoring') }}