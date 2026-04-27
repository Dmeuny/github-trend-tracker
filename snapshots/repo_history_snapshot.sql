{% snapshot repo_history_snapshot %}

{{
    config(
        target_schema='snapshots',
        unique_key='repo_id',
        strategy='check',
        check_cols=['stars', 'description', 'language', 'topic'],
    )
}}

select * from {{ ref('stg_github_repos') }}

{% endsnapshot %}