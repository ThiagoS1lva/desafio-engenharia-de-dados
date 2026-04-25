with source as (
    select *
    from {{ source('raw', 'tiktok_posts') }}
),

renamed as (
    select
        'tiktok'::text as platform,
        nullif(btrim(item_id::text), '') as content_id,
        nullif(btrim(business_username::text), '') as account_name,
        to_timestamp(nullif(btrim(create_time::text), '')::double precision) as published_at,
        'VIDEO'::text as content_format,
        nullif(btrim(likes::text), '')::integer as likes,
        nullif(btrim(comments::text), '')::integer as comments,
        nullif(btrim(shares::text), '')::integer as shares,
        nullif(btrim(video_views::text), '')::integer as video_views,
        nullif(btrim(reach::text), '')::integer as reach,
        nullif(btrim(favorites::text), '')::integer as favorites,
        nullif(btrim(profile_views::text), '')::integer as profile_views,
        nullif(btrim(new_followers::text), '')::integer as new_followers,
        nullif(btrim(total_time_watched::text), '')::integer as total_time_watched,
        nullif(btrim(average_time_watched::text), '')::numeric as average_time_watched,
        nullif(btrim(full_video_watched_rate::text), '')::numeric as full_video_watched_rate,
        nullif(btrim(video_duration::text), '')::numeric as video_duration,
        nullif(btrim(app_download_clicks::text), '')::integer as app_download_clicks,
        nullif(btrim(lead_submissions::text), '')::integer as lead_submissions,
        nullif(btrim(phone_number_clicks::text), '')::integer as phone_number_clicks,
        nullif(btrim(website_clicks::text), '')::integer as website_clicks,
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
    content_format,
    likes,
    comments,
    shares,
    video_views,
    reach,
    favorites,
    profile_views,
    new_followers,
    total_time_watched,
    average_time_watched,
    full_video_watched_rate,
    video_duration,
    app_download_clicks,
    lead_submissions,
    phone_number_clicks,
    website_clicks
from deduplicated
where row_number = 1
