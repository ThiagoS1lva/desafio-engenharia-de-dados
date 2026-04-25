with source as (
    select *
    from {{ source('raw', 'instagram_media_insights') }}
),

renamed as (
    select
        'instagram'::text as platform,
        nullif(btrim(id::text), '') as content_id,
        lower(nullif(btrim(content_source::text), '')) as content_source,
        nullif(btrim(likes::text), '')::integer as likes,
        nullif(btrim(reach::text), '')::integer as reach,
        nullif(btrim(saved::text), '')::integer as saved,
        nullif(btrim(views::text), '')::integer as views,
        nullif(btrim(shares::text), '')::integer as shares,
        nullif(btrim(follows::text), '')::integer as follows,
        nullif(btrim(comments::text), '')::integer as comments,
        nullif(btrim(replies::text), '')::integer as replies,
        nullif(btrim(profile_visits::text), '')::integer as profile_visits,
        nullif(btrim(total_interactions::text), '')::integer as total_interactions,
        nullif(btrim(_dlt_load_id::text), '') as _dlt_load_id,
        nullif(btrim(_dlt_id::text), '') as _dlt_id
    from source
),

deduplicated as (
    select
        *,
        row_number() over (
            partition by content_id
            order by _dlt_load_id desc nulls last, _dlt_id desc nulls last
        ) as row_number
    from renamed
    where content_id is not null
)

select
    platform,
    content_id,
    content_source,
    likes,
    reach,
    saved,
    views,
    shares,
    follows,
    comments,
    replies,
    profile_visits,
    total_interactions
from deduplicated
where row_number = 1
