with source as (
    select *
    from {{ source('raw', 'tiktok_comments') }}
),

renamed as (
    select
        'tiktok'::text as platform,
        nullif(btrim(post_id::text), '') as content_id,
        nullif(btrim(comment_id::text), '') as comment_id,
        replace(nullif(btrim(comment_timestamp::text), ''), ' UTC', '+00')::timestamptz as comment_timestamp,
        lower(nullif(btrim(predicted_sentiment::text), '')) as sentiment,
        nullif(btrim(confidence_sentiment::text), '')::numeric as confidence_sentiment,
        nullif(btrim(_dlt_load_id::text), '') as _dlt_load_id,
        nullif(btrim(_dlt_id::text), '') as _dlt_id
    from source
),

deduplicated as (
    select
        *,
        row_number() over (
            partition by comment_id
            order by comment_timestamp desc nulls last, _dlt_load_id desc nulls last, _dlt_id desc nulls last
        ) as row_number
    from renamed
    where comment_id is not null
)

select
    platform,
    content_id,
    comment_id,
    comment_timestamp,
    sentiment,
    confidence_sentiment
from deduplicated
where row_number = 1
