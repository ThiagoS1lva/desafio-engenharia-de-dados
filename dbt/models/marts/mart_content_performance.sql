with source as (
    select *
    from {{ ref('int_content__unified') }}
)

select
    platform,
    content_id,
    account_name,
    published_at,
    cast(published_at as date) as publish_date,
    extract(dow from published_at) as weekday,
    content_format,
    likes,
    comments,
    shares,
    reach,
    views,
    engagement_total,
    engagement_rate,
    video_duration
from source
