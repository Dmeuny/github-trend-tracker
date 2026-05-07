{% snapshot repo_history_snapshot %}
{{
    config(
        target_schema='snapshots',
        unique_key='repo_id',
        strategy='check',
        check_cols=['stars', 'description', 'language', 'topic'],
    )
}}
select 
    repo_id,
    name,
    description,
    language,
    stars,
    topic,
    fingerprint,
    start_date as loaded_at
from {{ source('github', 'repo_history') }}
where is_current = true
{% endsnapshot %}