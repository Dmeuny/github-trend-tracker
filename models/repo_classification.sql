{{ config(
    materialized='view'
) }}

select
    repo_id,
    name,
    de_score,
    ai_score,

CASE
    WHEN ai_score > de_score THEN 'AI'
    WHEN de_score > ai_score THEN 'DE'
    ELSE 'MIXED'
END

from {{ ref('repo_scoring') }}