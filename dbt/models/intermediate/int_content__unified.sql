with instagram as (
    select
        platform,
        content_id,
        account_name,
        published_at,
        content_format,
        likes,
        comments_count as comments,
        0 as shares,
        views as views,
        reach,
        saved as saves_or_favorites,
        profile_visits as profile_visits_or_profile_views,
        follows as new_followers_or_follows,
        total_interactions,
        null::numeric as video_duration
    from {{ ref('int_instagram__content_metrics') }}
),

tiktok as (
    select
        platform,
        content_id,
        account_name,
        published_at,
        content_format,
        likes,
        comments,
        shares,
        video_views as views,
        reach,
        favorites as saves_or_favorites,
        profile_views as profile_visits_or_profile_views,
        new_followers as new_followers_or_follows,
        null::integer as total_interactions,
        video_duration
    from {{ ref('int_tiktok__content_metrics') }}
)

select * from instagram
union all
select * from tiktok
