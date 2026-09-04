{{ config(
    materialized='view'
) }}

select
    repo_id,
    name,
    de_score,
    ai_score,

    case
        when ai_score >= de_score
             and ai_score >= 2
        then 'AI'

        when de_score > ai_score
             and de_score >= 2
        then 'DE'

        else 'OTHER'
    end as topic_reclassified

from {{ ref('repo_scoring') }}