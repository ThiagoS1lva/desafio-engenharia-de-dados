with media as (
    select *
    from {{ ref('stg_instagram__media') }}
),

insights as (
    select *
    from {{ ref('stg_instagram__insights') }}
)

select
    media.platform,
    media.content_id,
    media.account_name,
    media.published_at,
    media.content_source,
    media.media_type,
    media.content_format,
    media.like_count,
    media.comments_count,
    media.is_comment_enabled,
    insights.likes,
    insights.reach,
    insights.saved,
    insights.views,
    insights.shares,
    insights.follows,
    insights.comments,
    insights.replies,
    insights.profile_visits,
    insights.total_interactions
from media
left join insights
    on media.content_id = insights.content_id
