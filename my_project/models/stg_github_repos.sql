with source as (

    select * from {{ source('github', 'staging_cleaned') }}

),

renamed as (

    select
        repo_id,
        name,
        description,
        language,
        stars,
        topic,
        fingerprint,
        loaded_at

    from source

)

select * from renamed