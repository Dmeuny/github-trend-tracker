with current as (

    select *
    from {{ ref('repo_history_snapshot') }}
    where dbt_valid_to is null

),

previous as (

    select distinct on (repo_id)
        repo_id,
        stars as prev_stars
    from {{ ref('repo_history_snapshot') }}
    where dbt_valid_to is not null
    order by repo_id, dbt_valid_from desc

),

trends as (

    select
        c.repo_id,
        c.name,
        c.topic,
        c.stars                                                           as current_stars,
        p.prev_stars,
        c.stars - p.prev_stars                                            as star_growth,
        round(
            (c.stars - p.prev_stars)::numeric / nullif(p.prev_stars, 0) * 100,
            2
        )                                                                 as growth_pct,
        c.dbt_valid_from                                                  as last_updated

    from current c
    left join previous p on c.repo_id = p.repo_id

)

select *
from trends
order by star_growth desc nulls last
