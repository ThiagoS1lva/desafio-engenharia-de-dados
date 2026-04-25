with source as (
    select *
    from {{ source('raw', 'instagram_media') }}
),

renamed as (
    select
        'instagram'::text as platform,
        nullif(btrim(id::text), '') as content_id,
        nullif(btrim(username::text), '') as account_name,
        replace(nullif(btrim("timestamp"::text), ''), ' UTC', '+00')::timestamptz as published_at,
        lower(nullif(btrim(content_source::text), '')) as content_source,
        upper(nullif(btrim(media_type::text), '')) as media_type,
        upper(nullif(btrim(media_product_type::text), '')) as content_format,
        nullif(btrim(like_count::text), '')::integer as like_count,
        nullif(btrim(comments_count::text), '')::integer as comments_count,
        case lower(nullif(btrim(is_comment_enabled::text), ''))
            when 'true' then true
            when 'false' then false
            else null
        end as is_comment_enabled,
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
    account_name,
    published_at,
    content_source,
    media_type,
    content_format,
    like_count,
    comments_count,
    is_comment_enabled
from deduplicated
where row_number = 1
